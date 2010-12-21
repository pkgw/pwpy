/*
 *	autoflag.c David Whysong's automatic flagging program
 *
 * baseline 824 is Miriad ant 30-42
 *
 *	TODO:
 *	add a "thermal noise" measurement (just sum vis->thermal_sigmasq in quadrature)
 *
 *	WISHLIST:
 *	Threading for SMP machines
 *
 *	TODO:
 *
 *	-- do basic RFI flagging on non-calibrator files
 *
 *		Option to flag all data from a baseline/pol/chan if a certain percentage is flagged
 */


#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <complex.h>
#include <values.h>
#include <string.h>
#include <unistd.h>
#include <assert.h>
#include "mirclib.h"
#include "mirflib.h"
#include "hio.h"
#include "autoflag.h"
#include "list.h"

#define CORR_SIGMA 6.0
#define M_PI (3.141592653589793238462643383279502884197169399375105\
820974944592307816406286208998628034825342117067982148086513282306647L)

extern void options_c(char *, char *[], char *, int);

#define MAX_GAIN_ITERS 5

#define N_HEADER_PARAMS 6
#define N_OPTIONS 7
#define MAXCHAN 1024

/* A sidereal day is 23h 56m 4.09074s = 86164.09074 seconds */
#define SIDEREAL_DAY (86164.09074)
/* A Julian day is 24h = 86400 seconds */
#define JULIAN_DAY (86400.0)
#define SD_JD ((double) (SIDEREAL_DAY / JULIAN_DAY))

#define TRUE 1
#define FALSE 0
#define MIN(a,b) ((a)<(b)?(a):(b))
#define MAX(a,b) ((a)>(b)?(a):(b))

const char blank=0;
int one=1;
int maxsels=1024;
int n_vis_files=0, n_cal_files=0;
char noflag,noband,nophase,norfi,ata,nonoise,nodistro;
dataset_struct *visdata=NULL, *firstvisdata=NULL, *firstcaldata=NULL;
FILE *fd;


inline void set_flag(vis_struct *vis, int channel, int value) {
	unsigned char mask;
	unsigned int i;
	mask = 1<<(channel % 8);
	i = channel / 8;
	if (value) vis->flags[i] |= mask;
	else vis->flags[i] &= ~mask;
}


inline unsigned char good(vis_struct *vis, int channel) {
	unsigned char mask;

	mask = 1 << (channel % 8);
	mask = (mask & vis->flags[channel/8]) > 0;
	return mask;
}


// Returns a human-readable number representing binary flags for the first 10 channels
unsigned long int flags_to_int(vis_struct *vis) {
	unsigned long int exp=1, flags=0;
	int i,j;

	j = vis->visdata->n_chan;
	if (j>10) j=10;			// number of decimal digits for a 32 bit ulong
	for (i=0; i<j; i++) {
		if (good(vis,i)) flags += exp;
		exp *= 10;
	}
	return(flags);
}


inline unsigned int count_unflagged_chan(vis_struct *vis) {
	unsigned int count = 0;
	int i;

	for (i=0; i<vis->visdata->n_chan; i++)
		if (good(vis,i)) count++;

	return (count);
}


void dump_vis(vis_struct *vis) {
	fprintf(stderr,"\t%f\t%2.3f\t%2.3f\t%2.3f\t%d\t%d %d\t%lu\n",\
		86400*vis->time,crealf(vis->data[0]),cimagf(vis->data[0]),vis->thermal_sigmasq,vis->pol,vis->ant[0],vis->ant[1],flags_to_int(vis));
}

void dump_bin(bin_struct *bin) {
	vis_struct *vis;

	vis = bin->data;
	fprintf(stderr,"Dumping bin %p from file %s.\n",bin,vis->visdata->fname);
	fprintf(stderr,"\t%d ants, %d chan, %lu vis\n",vis->visdata->n_ants,vis->visdata->n_chan,bin->n_vis);
	fprintf(stderr,"\ttime\treal\timag\ts^2\tpol\tants\tflags\tflags\n");
	vis = bin->data;
	while (vis) {
		dump_vis(vis);
		vis = vis->next;
	}
}


/* Set things up to parse the "options" keyword */
void getopt_dave() {
	/* If you want to add a new option, you MUST increase the value of the N_OPTIONS #define. */
	char *opts[N_OPTIONS]={"noflag","noband","nophase","norfi","ata","nodist","nonoise"};
	char present[N_OPTIONS];

	options_c("options",opts,present,N_OPTIONS);
	noflag=present[0];
	noband=present[1];
	nophase=present[2];
	norfi=present[3];
	ata=present[4];
	nodistro=present[5];
	nonoise=present[6];
}


/* Note: pol must be 0 or 1; it is not equal to the MIRIAD polarization value */
void set_bin_flag(bin_struct *bin, char pol, int bl, unsigned chan, char value) {
	unsigned char mask;
	unsigned int i,idx;
#ifdef DEBUG
	if (pol > 1) bug_c('f',"Invalid polarization passed to set_bin_flag; must be 0 or 1.");
#endif
	i = pol*bin->visdata->n_bl*bin->visdata->n_chan + bl * bin->visdata->n_chan + chan;
	idx = i / 8;
	mask = 1 << (i % 8);
	if (value) bin->flags[idx] |= mask;
	else bin->flags[idx] &= ~mask;
}


// Returns 1 if the pol/bl/chan is bad
unsigned char get_bin_flag(bin_struct *bin, char pol, int bl, unsigned chan) {
	unsigned char mask;
	unsigned int i,idx;

	i = pol*bin->visdata->n_bl*bin->visdata->n_chan + bl * bin->visdata->n_chan + chan;
	idx = i / 8;
	mask = 1 << (i % 8);
	mask = (mask & bin->flags[idx]) > 0;
	return mask;
}


/*
 * Returns an index to an array of dimension (2 pols) x (n_baselines) x (n_channels)
 */
inline long indx(bin_struct *bin, int pol, int bl, unsigned chan) {
	int p;
	if (pol == bin->visdata->ppol1) p=0;
	else if (pol == bin->visdata->ppol2) p=1;
	else {
		bug_c('w',"Error: invalid polarization requested in indx");
		return(-1);
	}
#ifdef DEBUG
	unsigned int i = p*bin->visdata->n_bl*bin->visdata->n_chan + bl * bin->visdata->n_chan + chan;
	if ((i<0) || (i > 2*bin->visdata->n_bl*bin->visdata->n_chan)) {
		bug_c('f',"indx: value out of range");
	}
#endif
	return(p*bin->visdata->n_bl*bin->visdata->n_chan + bl * bin->visdata->n_chan + chan);
}


/*
 * This does NOT return the MIRIAD baseline number! It returns an array index.
 * Given ant1 and ant2, this returns a unique (and packed) index, with space for
 * autocorrelations.
 */
inline unsigned int get_bl(vis_struct *vis) {
	return (vis->visdata->n_ants*vis->ant[0]-(vis->ant[0]*(vis->ant[0]+1)/2) + vis->ant[1]);
}


// used by qsort
int cmp_num(const void *a, const void *b) {

	if (isnan(*(const float *)a) && isnan(*(const float *)b)) return 0;
	else if (isnan(*(const float *)a)) return 1;
	else if (isnan(*(const float *)b)) return -1;

	if (*(const float *)a < *(const float *)b) return -1;
	return *(const float *)a > *(const float *)b;
}


// Find the median of a list of floats.
// Flagged data should have value NAN.
float median_float(float *list, int n) {
	int i;

	qsort(list,n,sizeof(float),cmp_num);

	/* Find how many elements are not NAN */
	for (i=0; i<n; i++) if (isnan(list[i])) break;
	n=i;

	if (n == 0) return NAN;
	else if (n % 2 == 1) return list[n/2];
	else return ((list[n/2-1] + list[n/2]) / 2.0);
}


// Find median of a list of real and imaginary values separately
complex float median_cmplx(complex float *clist, int n) {
	float list[n];
	float re,im;
	int i;

	for (i=0; i<n; i++) list[i] = crealf(clist[i]);
	re = median_float(list,n);

	for (i=0; i<n; i++) list[i] = cimagf(clist[i]);
	im = median_float(list,n);

	if (isnan(re) || isnan(im)) return (NAN + NAN * I);
	else return re + im * I;
}


// Find the variance in a list of floats, emphasizing clean data. Flagged data
// should have value NAN. This works the same way as the deviation calculation
// in meddev_cmplx, but it finds the minimum deviation that encompasses 25% of
// the data (it's 50% in meddev_cmplx).
int meddev25_float(float *list, int n, float *med, float *dev) {
	int i, offset, len;

	qsort(list,n,sizeof(float),cmp_num);

	/* Find how many elements are not NaN */
	for (i=0; i<n; i++) if (isnan(list[i])) break;
	n=i;	// Effectively throw out NaN values

	if (n == 0) {	// No good data here. Return error.
		*dev = NAN;
		return(1);
	}
	else if (n % 2 == 1) *med = list[n/2];
	else *med = ((list[n/2-1] + list[n/2]) / 2.0);

	// Find deviation using the sorted list.
	offset = n/4;
	len = n-offset;
	float tmp[len];
	for (i=0; i<len; i++) tmp[i] = list[i+offset] - list[i];
	*dev = tmp[0];
	for (i=1; i<len; i++) if (tmp[i] < *dev) *dev=tmp[i];	// Use the smallest value from the list
	*dev /= 2.0;    // want half-width, not full-width

	return 0;
}


/* Find the variance of real and imaginary values separately, emphasizing clean data.
 * Inputs: complex float array *clist contains the data. Integer n is the length of the array.
 * Results are returned in *dev.
 */
void meddev25_cmplx(complex float *clist, int n, complex float *med, complex float *dev) {
	float list[n];
	float re,im,redev,imdev;
	int i,j=0;

	for (i=0; i<n; i++) list[i] = crealf(clist[i]);
	j+=meddev25_float(list,n,&re,&redev);

	for (i=0; i<n; i++) list[i] = cimagf(clist[i]);
	j+=meddev25_float(list,n,&im,&imdev);

	*med = re + im*I;
	*dev = redev + imdev*I;
}


// Find the variance in a list of floats, emphasizing
// noisy data. Flagged data should have value NAN.
int dev90_float(float *list, int n, float *dev) {
	int i, offset, len;

	qsort(list,n,sizeof(float),cmp_num);

	/* Find how many elements are not NaN */
	for (i=0; i<n; i++) if (isnan(list[i])) break;
	n=i;	// Effectively throw out NaN values

	if (n == 0) {	// No good data here. Return error.
		*dev = NAN;
		return(0);
	}

	// Find scatter using the sorted list.
	offset = n*9/10;
	len = n-offset;
	float tmp[len];
	for (i=0; i<len; i++) tmp[i] = list[i+offset] - list[i];
	*dev = tmp[0];
	for (i=1; i<len; i++) if (tmp[i] < *dev) *dev=tmp[i];	// Use the smallest value from the list
	*dev /= 2.0;	// want half-width, not full-width

	return n;	// return the number of good data
}


// Find the variance of real and imaginary values separately, emphasizing noisy data.
int dev90_cmplx(complex float *clist, int n, complex float *dev) {
	float list[n];
	float redev,imdev;
	int i,j,k;

	for (i=0; i<n; i++) list[i] = crealf(clist[i]);
	j=dev90_float(list,n,&redev);

	for (i=0; i<n; i++) list[i] = cimagf(clist[i]);
	k=dev90_float(list,n,&imdev);

	*dev = redev + imdev*I;

	if (j != k) return(-1);
	else return (j);	// return the number of good data
}




// Find the median and scatter of a list of floats. The scatter
// is calculated by taking the minumum spread which encompasses
// half of the data values.
// Flagged data should have value NAN.
int meddev_float(float *list, int n, float *med, float *dev) {
	int i, offset;

	qsort(list,n,sizeof(float),cmp_num);

	/* Find how many elements are not NaN */
	for (i=0; i<n; i++) if (isnan(list[i])) break;
	n=i;	// Effectively throw out NaN values

	if (n == 0) {	// No good data here. Return error.
		*med = NAN;
		*dev = NAN;
		return(1);
	}
	else if (n % 2 == 1) *med = list[n/2];
	else *med = ((list[n/2-1] + list[n/2]) / 2.0);

	// Now, find scatter. Use the sorted list.
	float tmp[n/2];
	offset = n/2;
	for (i=0; i<n/2; i++) tmp[i] = list[i+offset] - list[i];
	*dev = tmp[0];
	for (i=1; i<n/2; i++) if (tmp[i] < *dev) *dev=tmp[i];	// Use the smallest value from the list
	*dev /= 2.0;    // want half-width, not full-width

	return 0;
}


/* Find median of real and imaginary values separately */
int meddev_cmplx(complex float *clist, int n, complex float *med, complex float *dev) {
	float list[n];
	float re,im,redev,imdev;
	int i,j=0;

	for (i=0; i<n; i++) list[i] = crealf(clist[i]);
	j+=meddev_float(list,n,&re,&redev);

	for (i=0; i<n; i++) list[i] = cimagf(clist[i]);
	j+=meddev_float(list,n,&im,&imdev);

	*med = re + im*I;
	*dev = redev + imdev*I;

	return 0;
}


// Compute the median value of the spectrum, for each pol/baseline
void meddevspec(unsigned int n_bl, unsigned int n_chan, complex float *med_spec, complex float *median, complex float *deviation) {
	unsigned int i,j,idx;

	for (i=0; i<2; i++)
	for (j=0; j<n_bl; j++) {
		idx = i*n_bl*n_chan + j*n_chan;		// Channel 0
		meddev_cmplx(&(med_spec[idx]),n_chan,&(median[i*n_bl+j]),&(deviation[i*n_bl+j]));
	}
}


/*
 * Check for spectral corruption.
 * Alternate algorithm: we compute a deviation for the entire spectrum using
 * meddev25_cmplx(). This is the minumum deviation that spans 1/4 of the sorted
 * data. Then, for each of the 4 windows, count the number of outling channels
 * treating real and imaginary values separately.
 */
void corrupt2(bin_struct *bin, unsigned int n_blocks, unsigned int *count) {
	unsigned int pol, ch, bl, n_bl, n_ants, n_chan, ant1, ant2, idx, i, width;
	complex float med, dev, tmplo, tmphi;

	n_bl = bin->visdata->n_bl;
	n_ants = bin->visdata->n_ants;
	n_chan = bin->visdata->n_chan;

	width = n_chan / n_blocks;
	if (n_chan % width > 0) {
		fprintf(stderr,"Error: spectrum does not divide evenly into %u blocks\n",n_blocks);
		abort();
	}
	if (width < 4) return;

	// Compute a variance estimate for every quarter of the spectrum; store in blkdev[i]
	for (pol=0; pol<2; pol++)
	for (ant1=0; ant1 < n_ants; ant1++)
	for (ant2=ant1+1; ant2 < n_ants; ant2++) {	// doesn't include autocorrelations
		bl = n_ants*ant1-(ant1*(ant1+1)/2) + ant2;

		// Compute the variance in the spectrum
		idx = pol*n_bl*n_chan + bl*n_chan;	// channel 0
		meddev25_cmplx(&(bin->med_spec[idx]),n_chan,&med,&dev);
//		idx = pol * n_bl + bl;
//		med = bin->median[idx];
//		dev = bin->deviation[idx];

		// Increase the count for each outlier pol/baseline/channel
		tmplo = bin->median[pol*n_bl+bl] - CORR_SIGMA * dev;
		tmphi = bin->median[pol*n_bl+bl] + CORR_SIGMA * dev;
		for (ch = 0; ch <= n_chan; ch++) {
			i = ch / width;	// block number
			idx = pol*n_bl*n_chan + bl*n_chan + ch;

			if (crealf(bin->med_spec[idx]) > crealf(tmphi - bin->rms_spec[idx]) || \
			    crealf(bin->med_spec[idx]) < crealf(tmplo + bin->rms_spec[idx]) || \
			    cimagf(bin->med_spec[idx]) > cimagf(tmphi - bin->rms_spec[idx]) || \
			    cimagf(bin->med_spec[idx]) < cimagf(tmplo + bin->rms_spec[idx])) {
				count[pol*n_ants*n_blocks + ant1*n_blocks + i]++;
				count[pol*n_ants*n_blocks + ant2*n_blocks + i]++;
			}
		}
	}
}


/*
 * Check for spectral corruption. The spectrum is divided into blocks, and the
 * variance in each block is compared against the others.
 */
void corrupt(bin_struct *bin, unsigned int n_blocks, unsigned int *count) {
	unsigned int start, end, pol, bl, n_bl, n_ants, n_chan, ant1, ant2, idx, i, j, width;
	complex float dev[n_blocks], tmp;
	int n;

	n_bl = bin->visdata->n_bl;
	n_ants = bin->visdata->n_ants;
	n_chan = bin->visdata->n_chan;

	width = n_chan / n_blocks;
	if (n_chan % width > 0) printf("Warning: spectrum does not divide evenly into %u blocks\n",n_blocks);
	if (width < 4) return;

	// Compute a variance estimate for every quarter of the spectrum; store in dev[i]
	for (pol=0; pol<2; pol++)
	for (ant1=0; ant1 < n_ants; ant1++)
	for (ant2 = ant1+1; ant2 < n_ants; ant2++) {
		bl = n_ants*ant1-(ant1*(ant1+1)/2) + ant2;
		for (i=0; i<n_blocks; i++) {
			start = i * n_chan / n_blocks;

			idx = pol*n_bl*n_chan + bl*n_chan + start;
			// Compute the variance in the window of our spectrum
			n = dev90_cmplx(&(bin->med_spec[idx]),width,&dev[i]);

			if (n<10) {	// Not enough data remaining to get a good deviation
				dev[i] = NAN + NAN*I;
			}
			else {
				// Compute the channel-median of the time-series deviations
				tmp = median_cmplx(&(bin->rms_spec[idx]),width);
				// Add in quadrature, treating real and imag seperately.
				dev[i] = sqrt(crealf(dev[i])*crealf(dev[i])+crealf(tmp)*crealf(tmp)) + I*sqrt(cimagf(dev[i])*cimagf(dev[i])+cimagf(tmp)*cimagf(tmp));
			}
		}

		// Compare variances between quarters of the spectrum, and
		// increase the count for each antpol/channel-region that is
		// high. NaN values do not cause problems here.
		for (i=0; i<n_blocks; i++)
		for (j=0; j<n_blocks; j++) {
			if (i==j) continue;
			else if ((crealf(dev[i]) > 3.0 * crealf(dev[j])) || \
				 (cimagf(dev[i]) > 3.0 * cimagf(dev[j]))) {
					count[pol*n_ants*n_blocks + ant1*n_blocks + i]++;
					count[pol*n_ants*n_blocks + ant2*n_blocks + i]++;
			}
		}
	}
}




/*
 * Flatten the bandpasses
 *
 * Computes a bandpass for each antenna using the medians. Flags noisy data on
 * baselines that contribute to solutions that are not converging quickly.
 *
 * Minimize the function:
 *    F = Sum_bl ( gain(ant1)(ch) * conj gain(ant2)(ch) * data(i,j)(chan) - median(bl)(ch) )^2
 * by varying gains[n_pol][n_ant][n_chan]
 *
 * Minimum is at: gain[pol][ant1][ch] = csqrtf(median[bl] / median[bl][ch]) / conjf(gain[pol][ant2][ch])
 */
complex float *bpcal(bin_struct *bin, complex float *med, complex float *median, complex float *rms) {
	complex float *gainlist; // [2][n_ants][n_ants-1][n_chan];	// List of all possible gain solutions; every antenna vs. every other antenna
	unsigned int n_bl = bin->visdata->n_bl;
	unsigned int n_ants = bin->visdata->n_ants;
	unsigned int n_chan = bin->visdata->n_chan;
	complex float glist[2][n_ants-1];
	complex float *gain, tmpgain;
	complex float medrms;
	unsigned int ch, bl, idx, idx2, idx_bl, niter=1, n, nbad;
	unsigned int ant, ant1, ant2, nflag=0;
	int i, pol;
	float maxdev, meddev;			// Greatest change in any gain in the most recent iteration
	float dev[2*n_ants*n_chan];		// Change in gain in the most recent iteration
	char done=0;
	char check[2*n_ants*n_chan];		// Antpol/channels which are converging slowly

	inline unsigned int gainidx(int pol, int ant1, int ant2, unsigned int ch) {
		return pol * n_ants * (n_ants-1) * n_chan + ant1 * (n_ants-1) * n_chan + ant2 * n_chan + ch;
	}

	gain = malloc(sizeof(complex float) * 2 * n_ants * n_chan);
	gainlist = malloc(sizeof(complex float) * 2 * n_ants * (n_ants-1) * n_chan);
	if (!gain || !gainlist) bug_c('f',"Out of memory in function bpcal.");
	for (i=0; i<2*n_ants*n_chan; i++) gain[i] = 1.0 + 0.0 * I;
	for (pol=0; pol<2; pol++)
	  for (ant1=0; ant1<n_ants; ant1++)
	  for (ant2=0; ant2<n_ants-1; ant2++)
	  for (ch=0; ch<n_chan; ch++) {
		gainlist[gainidx(pol,ant1,ant2,ch)] = NAN + NAN * I;
	}

	printf("Starting bandpass calibration loop\n");
	printf("    MedDev\tMaxDev\t#outliers\n");
	while (!done) {
		medrms = median_cmplx(rms,2*n_bl*n_chan);
		/* For each antpol, make a list of all contributing baselines, stored in "gainlist" */
		for (pol=0; pol<2; pol++)
		for (ant=0; ant<n_ants; ant++) {
			i=0;
			ant2 = ant;
			for (ant1 = 0; ant1 < ant2; ant1++)
		  	for (ch=0; ch<n_chan; ch++) {
					bl = n_ants*ant1-(ant1*(ant1+1)/2) + ant2;
					idx_bl = pol*n_bl*n_chan + bl * n_chan + ch;
					idx = pol*n_ants*n_chan + ant1 * n_chan + ch;
					// Conjugate, since we're getting solutions for ant == ant2
					gainlist[gainidx(pol,ant,ant1,ch)] = conjf(csqrtf(median[pol*n_bl+bl] / med[idx_bl]) / gain[idx]);
					i++;
			}
			ant1 = ant;
			for (ant2 = ant1+1; ant2 < n_ants; ant2++)
		  	for (ch=0; ch<n_chan; ch++) {
					bl = n_ants*ant1-(ant1*(ant1+1)/2) + ant2;
					idx_bl = pol*n_bl*n_chan + bl * n_chan + ch;
					idx = pol*n_ants*n_chan + ant2 * n_chan + ch;
					gainlist[gainidx(pol,ant,ant2,ch)] = csqrtf(median[pol*n_bl+bl] / med[idx_bl]) / conjf(gain[idx]);
					i++;
			}
		}

		/*
	 	* Now, iterate toward a solution. If we find outlying data we can flag it.
	 	* Be wary, the data have NaN values present (if all data for that antpol/chan were flagged)
	 	*/
		nbad = 0;
		n=0;
		for (i=0; i<2*n_ants*n_chan; i++) dev[i] = NAN;
		printf("  %d ",niter);
		for (pol=0; pol<2; pol++)
	  	for (ant=0; ant<n_ants; ant++)
	  	for (ch=0; ch<n_chan; ch++) {
			// Find median value for the new gain; use it.
			i=0;
			for (ant1=0; ant1<n_ants; ant1++) {
				if (ant == ant1) continue;
				glist[pol][i] = gainlist[gainidx(pol,ant,ant1,ch)];
				i++;
			}
			idx = pol*n_ants*n_chan + ant*n_chan + ch;
			tmpgain = (median_cmplx(glist[pol], n_ants-1) + gain[idx]) / 2.0;
			dev[idx] = cabsf(tmpgain - gain[idx]);
			if (isnan(tmpgain)) continue;
			gain[idx] = tmpgain;
			n++;
		}

		maxdev = 0.0;
		meddev = median_float(dev,2*n_ants*n_chan);
		printf("%.4f\t",meddev);
		for (i=0; i<2*n_ants*n_chan; i++) {
			if (dev[i] > maxdev) maxdev = dev[i];
			if (dev[i] > 5*meddev) nbad++;
		}
		printf(" %.2f",maxdev);
		printf("  %u of %u\t",nbad,n);

		nbad=0;
		/* Start looking for things to flag if we're getting close to convergence */
		if (meddev < 0.01) {
			for (i=0; i<2*n_ants*n_chan; i++) {
				if (dev[i] > 5*meddev) {
					nbad++;
					check[i]=1;
				}
				else check[i]=0;
			}
			printf("Looking carefully at %d antpol/chans\t",nbad);

			for (pol=0; pol<2; pol++)
			for (ant1=0; ant1 < n_ants; ant1++)
			for (ant2 = ant1+1; ant2 < n_ants; ant2++)
		  	for (ch=0; ch<n_chan; ch++) {
				bl = n_ants*ant1-(ant1*(ant1+1)/2) + ant2;
				idx_bl = pol*n_bl*n_chan + bl * n_chan + ch;
				idx = pol*n_ants*n_chan + ant1 * n_chan + ch;	// antenna-based index for ant1
				idx2 = pol*n_ants*n_chan + ant2 * n_chan + ch;	// antenna-based index for ant2
				if (check[idx] || check[idx2]) {
					if (cabsf(rms[idx_bl]) > 3 * cabsf(medrms)) {
						nflag++;
						set_bin_flag(bin, pol, bl, ch, 1);
						med[idx_bl] = NAN + NAN * I;
						rms[idx_bl] = NAN + NAN * I;
						idx_bl = pol*n_bl*n_chan + bl*n_chan;	// channel 0
						median[pol*n_bl+bl] = median_cmplx(&(med[idx_bl]), n_chan);	// recompute spectral median
					}
				}
			}
			if (nflag) printf("  %u bl/pol/chan marked bad",nflag);
			printf("\n");
		}
		else printf("\n");

		niter++;
		if (maxdev < 0.01) done=1;
			else if (niter > 10) {
			printf("Reached maximum number of iterations.\n");
			done=1;
		}
		else done=0;
		//printf("\n");
	}
	free(gainlist);

	return gain;
}

#include <fcntl.h>
void write_spectrum(bin_struct *bin, char *name) {
	FILE *fd;
	int i,bl,ch,idx;
	fd = fopen(name,"a");

	for (i=0; i<2; i++)
	for (bl=0; bl<bin->visdata->n_bl; bl++)
	for (ch=0; ch<bin->visdata->n_chan; ch++) {
		idx = i*bin->visdata->n_bl*bin->visdata->n_chan + bl * bin->visdata->n_chan + ch;
		fprintf(fd,"%d %d %d %f %f\n",i,bl,ch,crealf(bin->med_spec[idx]),cimagf(bin->med_spec[idx]));
	}
	fprintf(fd,"\n");
	fclose(fd);
}


/* Duplicate of function PolsC2P from $MIRSUBS/pols.for.
 * I'm not sure how to call that from C.
 * Value is returned in *str, which must have dimension 3. */
void getpolstr(dataset_struct *visdata, int p, char *str) {
	char polstr[26]="YXXYYYXXLRRLLLRRxxI Q U V ";
	int idx;

	if (p==0) idx = (visdata->ppol1 + 8) * 2;
	else if (p==1) idx = (visdata->ppol2 + 8) * 2;
	else {
		fprintf(stderr,"Error: getpol: Invalid polarization.\n");
		abort();
	}
	if (idx < 0 || idx > 24) {
		fprintf(stderr,"Error: getpol: Invalid polarization stored in the dataset_struct.\n");
		abort();
	}
	str = strncpy(str, polstr+idx, 2);
	str[2] = '\0';
}


/*
 * Determine flags from a calibrator scan.
 */
void calflag(bin_struct *bin) {
	vis_struct *vis;
	complex float *med_spec, *rms_spec, *median, *deviation;
	complex float **data;
	unsigned *n, *n_bad, n_chan, nflag=0, start, end;
	int i,j,n_bl,bl, ant1, ant2;
	register unsigned idx, idx2, idx_bl, ch;
	unsigned int n_ants = bin->visdata->n_ants;
	unsigned int *nhigh;

	vis = bin->data;
	n_chan = vis->visdata->n_chan;
	n_bl = vis->visdata->n_bl;
	med_spec  = malloc(sizeof(complex float) * 2 * n_bl * n_chan);
	rms_spec  = malloc(sizeof(complex float) * 2 * n_bl * n_chan);
	n = malloc(sizeof(unsigned) * 2 * n_bl * n_chan);
	n_bad = malloc(sizeof(unsigned) * 2 * n_bl * n_chan);
	median = malloc(sizeof(complex float) * 2 * n_bl);
	deviation = malloc(sizeof(complex float) * 2 * n_bl);
	if (!median || !deviation || !n || !med_spec || !rms_spec) bug_c('f',"Out of memory in function calflag.");

	bin->med_spec = med_spec;
	bin->rms_spec = rms_spec;
	bin->median = median;
	bin->deviation = deviation;


	// Initialization
	for (i=0; i<2*n_bl*n_chan; i++) {
		n[i]=0;
		n_bad[i]=0;
		med_spec[i]=NAN + NAN*I;
		rms_spec[i]=NAN + NAN*I;
	}

	/* Compute the number of data elements in each pol/baseline/channel */
	for (i=0; i<n_chan; i++) {
		vis = bin->data;
		while (vis) {	// Do the sum for this channel. Includes both pols and all baselines.
			bl = get_bl(vis);
			idx = indx(bin,vis->pol,bl,i);
			if (good(vis,i)) n[idx]++;
			else n_bad[idx]++;
			vis = vis->next;
		}
	}
	/* Set the bin flag if less than 50% of the loaded data are good. */
	for (i=0; i<2; i++)
	for (bl=0; bl<n_bl; bl++)
	for (ch=0; ch<n_chan; ch++) {
		idx = i*n_bl*n_chan + bl * n_chan + ch;
		if (n[idx] < n_bad[idx]) {
			set_bin_flag(bin,i,bl,ch,1);
			nflag++;
		}
	}
	printf("%u pol/baseline/channels are already substantially or completely flagged. Marking these as bad.\n",nflag);
	free(n_bad);

	/* Make an array of median amplitudes for each pol/bl/chan. */
	/* Make a temporary array of arrays to hold the data */
	data = malloc(sizeof(complex float *) * n_bl * n_chan * 2);
	if (!data) bug_c('f',"Out of memory in function calflag.");
	for (i=0; i<2*n_bl*n_chan; i++) {
		data[i] = malloc(sizeof(complex float) * n[i]);
		if (!data[i]) bug_c('f',"Out of memory in function calflag.");
		/* Initialize each array to an invalid number */
		for (j=0; j<n[i]; j++) {
			data[i][j] = NAN + NAN*I;
		}
	}

	/*
	 * Fill the data. First make an array of lists of data values. Then sort, then get the median.
	 * Karto normalizes each pol/bl/chan by the geometric mean of the two
	 * autocorrelations (2 antennas per baseline). I do a bandpass cal instead.
	 */
	for (i=0; i<n_chan; i++) {
		vis = bin->data;
		while (vis) {	// Do the sum for this channel. Includes both pols and all baselines.
			if (good(vis,i)) {
				bl = get_bl(vis);
				idx = indx(bin,vis->pol,bl,i);
				for (j=0; j<n[idx]; j++) {
					if (isnan(data[idx][j])) {
						data[idx][j] = vis->data[i];
						break;
					}
				}
			}
			vis = vis->next;
		}
	}

	// Get median and scatter
        for (i=0; i<2*n_bl*n_chan; i++) meddev_cmplx(data[i],n[i],&(med_spec[i]),&(rms_spec[i]));

	// Compute a channel median for each baseline.
	meddevspec(n_bl, n_chan, med_spec, median, deviation);


	// FIXME. This only does time-series analysis, within a single scan. Not much data to work with!
	// It would be useful to look across the spectrum (i.e. use deviation in addition to rms_spec), BUT
	// we must avoid flagging spectral corruption here, otherwise the corruption routine won't work.
	if (!norfi) {
		// Flag RFI
		nhigh=malloc(sizeof(unsigned) * 2*n_bl*n_chan);
		for (i=0; i<2*n_bl*n_chan; i++) nhigh[i]=0;
		// Count the number of outlying values for each pol/baseline/channel.
		float tmplo, tmphi;
		for (i=0; i<2*n_bl*n_chan; i++) {
			if (n[i]) {
				for (j=0; j<n[i]; j++) {
					tmplo = crealf(med_spec[i]) - 4 * crealf(rms_spec[i]);
					tmphi = crealf(med_spec[i]) + 4 * crealf(rms_spec[i]);
					if (crealf(data[i][j]) > tmphi || crealf(data[i][j]) < tmplo) nhigh[i]++;

					tmplo = cimagf(med_spec[i]) - 4 * cimagf(rms_spec[i]);
					tmphi = cimagf(med_spec[i]) + 4 * cimagf(rms_spec[i]);
					if (cimagf(data[i][j]) > tmphi || cimagf(data[i][j]) < tmplo) nhigh[i]++;
				}
			}
		}


		// Now, flag offending pol/baseline/channels. Also flag adjacent channels.
		nflag=0;
		for (bl=0; bl<n_bl; bl++)
		for (i=0; i<n_chan; i++) {
			idx = indx(bin,bin->visdata->ppol1,bl,i);
			if (nhigh[idx] > 0.6 * n[idx]) {
				if (!get_bin_flag(bin,0,bl,i)) {
					nflag++;
					set_bin_flag(bin,0,bl,i,1);
					free(data[idx]);
					data[idx] = NULL;
					n[idx] = 0;
					rms_spec[idx] = NAN + NAN * I;
					med_spec[idx] = NAN + NAN * I;
				}
				// Flag adjacent channels too.
				j=i-1;
				if ((j > 0) && !get_bin_flag(bin,0,bl,j))  {
					idx = indx(bin,bin->visdata->ppol1,bl,j);
					nflag++;
					set_bin_flag(bin,0,bl,j,1);
					free(data[idx]);
					data[idx] = NULL;
					n[idx] = 0;
					rms_spec[idx] = NAN + NAN * I;
					med_spec[idx] = NAN + NAN * I;
				}
				j=i+1;
				if ((j < n_chan) && !get_bin_flag(bin,0,bl,j)) {
					idx = indx(bin,bin->visdata->ppol1,bl,j);
					nflag++;
					set_bin_flag(bin,0,bl,j,1);
					free(data[idx]);
					data[idx] = NULL;
					n[idx] = 0;
					rms_spec[idx] = NAN + NAN * I;
					med_spec[idx] = NAN + NAN * I;
				}
			}
			idx = indx(bin,bin->visdata->ppol2,bl,i);
			if (nhigh[idx] > 0.6 * n[idx]) {
				if (!get_bin_flag(bin,1,bl,i)) {
					nflag++;
					set_bin_flag(bin,1,bl,i,1);
					free(data[idx]);
					data[idx] = NULL;
					n[idx] = 0;
					rms_spec[idx] = NAN + NAN * I;
					med_spec[idx] = NAN + NAN * I;
				}
				// Flag adjacent channels too.
				j=i-1;
				if ((j > 0) && !get_bin_flag(bin,1,bl,j)) {
					idx = indx(bin,bin->visdata->ppol2,bl,j);
					nflag++;
					set_bin_flag(bin,1,bl,j,1);
					free(data[idx]);
					data[idx] = NULL;
					n[idx] = 0;
					rms_spec[idx] = NAN + NAN * I;
					med_spec[idx] = NAN + NAN * I;
				}
				j=i+1;
				if ((j < n_chan) && !get_bin_flag(bin,1,bl,j)) {
					idx = indx(bin,bin->visdata->ppol2,bl,j);
					nflag++;
					set_bin_flag(bin,1,bl,j,1);
					free(data[idx]);
					data[idx] = NULL;
					n[idx] = 0;
					rms_spec[idx] = NAN + NAN * I;
					med_spec[idx] = NAN + NAN * I;
				}
			}
		}
		free(nhigh);
		printf("Flagged %u baseline/pol/channels that show exessive time variance.\n",nflag);
	}


	if (!noband) {
//write_spectrum(bin,"med.spec");
		// Do a bandpass calibration to flatten the spectrum.
		// The gains array has dimensions [2 pols][n_ants][n_chan]
		bin->gains = bpcal(bin, med_spec, median, rms_spec);
		// Apply the gains
		for (i=0; i<2; i++)
		for (ant1=0; ant1 < n_ants; ant1++)
		for (ant2 = ant1+1; ant2 < n_ants; ant2++) {
			bl = n_ants*ant1-(ant1*(ant1+1)/2) + ant2;
  			for (ch=0; ch<n_chan; ch++) {
				idx_bl = i*n_bl*n_chan + bl * n_chan + ch;
				idx = i*n_ants*n_chan + ant1 * n_chan + ch;	// antenna-based index for ant1
				idx2 = i*n_ants*n_chan + ant2 * n_chan + ch;	// antenna-based index for ant2
				for (j=0; j<n[idx_bl]; j++) data[idx_bl][j] *= bin->gains[idx] * ~ bin->gains[idx2];
			}
		}
		// Apply the flags found in bpcal
        	for (i=0; i<2; i++)
		for (bl=0; bl<n_bl; bl++)
		for (ch=0; ch<n_chan; ch++)
		if (get_bin_flag(bin,i,bl,ch)) {
			idx = i*n_bl*n_chan + bl * n_chan + ch;
			free(data[idx]);
			data[idx] = NULL;
			n[idx] = 0;
		}
	}
	// Re-calculate median and scatter, and channel median for each baseline
// FIXME this may cause difficulties for the spectral corruption routine, as the worst of the corruption will
// probably be flagged by the RFI algorithm. Not a problem until we re-calculate the statistics with medevspec()...
        for (i=0; i<2*n_bl*n_chan; i++) meddev_cmplx(data[i],n[i],&(med_spec[i]),&(rms_spec[i]));
	meddevspec(n_bl, n_chan, med_spec, median, deviation);

//write_spectrum(bin,"cal-med.spec");

	if (ata) {
		// Look for spectral corruption. This can be time dependent.
		// When flagging spectral corruption, the ENTIRE ANTENNA is affected.
		printf("Scanning for ATA specral corruption:\n");
		fflush(stdout);
		nhigh=malloc(sizeof(unsigned) * 2*n_ants*4);
		if (!nhigh) bug_c('f',"Out of memory.");
		nflag=0;
		char str[3];
		int max;

		while (1) {
			for (i=0; i<2*n_ants*4; i++) nhigh[i]=0;
			corrupt(bin,4,nhigh);
			max=0;
			for (i=0; i<2*n_ants*4; i++) if (nhigh[i] > max) max = nhigh[i];
			if (max == 0) break;

			for (ant1=0; ant1 < n_ants; ant1++)
			for (i=0; i<2; i++)
			for (j=0; j<4; j++) {
				idx  = i*n_ants*4 + ant1 * 4 + j;	// antenna-based index to the quarter spectral window
				getpolstr(bin->visdata,i,str);
				if (nhigh[idx] >= max) printf("  Spectral corruption found on antpol %d-%s, quarter %d\n",ant1+1,str,j);
			}

			// Flag the worst offender
			for (i=0; i<2; i++)
			for (ant1=0; ant1 < n_ants; ant1++)
			for (ant2 = ant1+1; ant2 < n_ants; ant2++) {
				bl = n_ants*ant1-(ant1*(ant1+1)/2) + ant2;
				for (j=0; j<4; j++) {
					idx  = i*n_ants*4 + ant1 * 4 + j;
					idx2 = i*n_ants*4 + ant2 * 4 + j;
					if (nhigh[idx] >= max || nhigh[idx2] >= max) {	// Found spectral corruption
						start = j * n_chan / 4;
						end = (j+1) * n_chan / 4;
  						for (ch=start; ch<end; ch++) {
							set_bin_flag(bin,i,bl,ch,1);
							idx_bl = i*n_bl*n_chan + bl * n_chan + ch;
							free(data[idx_bl]);
							data[idx_bl] = NULL;
							n[idx_bl] = 0;
							nflag++;
							rms_spec[idx_bl] = NAN + NAN * I;
							med_spec[idx_bl] = NAN + NAN * I;
						}
					}
				}
			}
			// Re-compute the channel-averaged stats after flagging
			meddevspec(n_bl, n_chan, med_spec, median, deviation);
		}
		free(nhigh);
		printf("  Flagged %u baseline/pol/channels.\n",nflag);
	}


	if (!nodistro) {
		printf("Looking at distribution of data in real/imag space:");
		// Flag discrepant data by looking at scatter in real/imag space.
		nflag=0;
		for (i=0; i<2; i++)
		for (bl=0; bl<n_bl; bl++) {
			// re-compute median and deviation of the spectrum
			idx = i*n_bl*n_chan + bl*n_chan;		// Channel 0
			meddev_cmplx(&(med_spec[idx]),n_chan,&(median[i*n_bl+bl]),&(deviation[i*n_bl+bl]));
			for (ch=0; ch<n_chan; ch++) {
				idx = i*n_bl*n_chan + bl*n_chan + ch;
				if (n[idx] == 0) continue;
				// re-compute the median and deviation in time
				meddev_cmplx(data[idx],n[idx],&(med_spec[idx]),&(rms_spec[idx]));
				// Subtract off the median value of each baseline, so we're centered at 0,0
				med_spec[idx] -= median[i*n_bl+bl];
				// Flag outliers
				if (cabsf(med_spec[idx])+cabsf(rms_spec[idx]) > 5.0 * cabsf(deviation[i*n_bl+bl])) {
					nflag++;
					set_bin_flag(bin,i,bl,ch,1);
					free(data[idx]);
					data[idx] = NULL;
					n[idx] = 0;
					rms_spec[idx] = NAN + NAN * I;
					med_spec[idx] = NAN + NAN * I;
				}
			}
		}
		printf(" flagged %u discrepant baseline/pol/channels.\n",nflag);
	}


	if (!nonoise) {
		// Re-calculate median and scatter, and channel median for each baseline
		printf("Looking for excessively noisy baselines:");
        	for (i=0; i<2*n_bl*n_chan; i++) meddev_cmplx(data[i],n[i],&(med_spec[i]),&(rms_spec[i]));
		meddevspec(n_bl, n_chan, med_spec, median, deviation);
		// Flag entire baselines if the deviation is > 3 times the median deviation
		nflag=0;
		complex float maxdev = median_cmplx(deviation,n_bl);
		for (i=0; i<2; i++)
		for (bl=0; bl<n_bl; bl++) {
			idx = i*n_bl+bl;
			if (crealf(deviation[idx]) > 3.0 * crealf(maxdev) || cimagf(deviation[idx]) > 3.0 * cimagf(maxdev)) {
				nflag++;
				for (ch=0; ch<n_chan; ch++) {
					idx = i*n_bl*n_chan + bl*n_chan+ch;
					if (n[idx]==0) continue;
					set_bin_flag(bin,i,bl,ch,1);
					free(data[idx]);
					data[idx] = NULL;
					n[idx] = 0;
					rms_spec[idx] = NAN + NAN * I;
					med_spec[idx] = NAN + NAN * I;
				}
			}
		}
		printf(" flagged %u baseline/pols.\n",nflag);
	}

	// Clean up
	for (i=0; i<2*n_bl*n_chan; i++) {
		free(data[i]);	// it's safe to call free(NULL)
	}
	free(data);
	free(n);
}


void noncal_stats(dataset_struct *visdata) {
	bin_struct *bin;
	vis_struct *vis;
	complex float *med_spec, *rms_spec, *median, *deviation;
	complex float **data;
	unsigned *n, *n_bad, n_chan, nflag=0;
	int i,j,n_bl,bl;
	register unsigned idx, ch;

	bin = visdata->bin;
	while (bin) {

		vis = bin->data;
		n_chan = vis->visdata->n_chan;
		n_bl = vis->visdata->n_bl;
		med_spec  = malloc(sizeof(complex float) * 2 * n_bl * n_chan);
		rms_spec  = malloc(sizeof(complex float) * 2 * n_bl * n_chan);
		n = malloc(sizeof(unsigned) * 2 * n_bl * n_chan);
		n_bad = malloc(sizeof(unsigned) * 2 * n_bl * n_chan);
		if ((!n) || (!med_spec) || (!rms_spec)) bug_c('f',"Out of memory in function noncal_stats.");

		// Initialization
		for (i=0; i<2*n_bl*n_chan; i++) {
			n[i]=0;
			n_bad[i]=0;
			med_spec[i]=NAN + NAN*I;
			rms_spec[i]=NAN + NAN*I;
		}

		/* Compute the number of data elements in each pol/baseline/channel */
		for (i=0; i<n_chan; i++) {
			vis = bin->data;
			while (vis) {	// Do the sum for this channel. Includes both pols and all baselines.
				bl = get_bl(vis);
				idx = indx(bin,vis->pol,bl,i);
				if (good(vis,i)) n[idx]++;
				else n_bad[idx]++;
				vis = vis->next;
			}
		}
		/* Set the bin flag if less than 50% of the loaded data are good. */
		for (i=0; i<2; i++)
		for (bl=0; bl<n_bl; bl++)
		for (ch=0; ch<n_chan; ch++) {
			idx = i*n_bl*n_chan + bl * n_chan + ch;
			if (n[idx] < n_bad[idx]) {
				set_bin_flag(bin,i,bl,ch,1);
				nflag++;
			}
		}
		printf("%u pol/baseline/channels are already substantially or completely flagged. Marking these as bad.\n",nflag);
		free(n_bad);

		/* Make an array of median amplitudes for each pol/bl/chan. */
		/* Make a temporary array of arrays to hold the data */
		data = malloc(sizeof(complex float *) * n_bl * n_chan * 2);
		if (!data) bug_c('f',"Out of memory in function calflag.");
		for (i=0; i<2*n_bl*n_chan; i++) {
			data[i] = malloc(sizeof(complex float) * n[i]);
			if (!data[i]) bug_c('f',"Out of memory in function calflag.");
			/* Initialize each array to an invalid number */
			for (j=0; j<n[i]; j++) {
				data[i][j] = NAN + NAN*I;
			}
		}

		/* Fill the data. First make an array of lists of data values. Then sort, then get the median.  */
		for (i=0; i<n_chan; i++) {
			vis = bin->data;
			while (vis) {	// Do the sum for this channel. Includes both pols and all baselines.
				if (good(vis,i)) {
					bl = get_bl(vis);
					idx = indx(bin,vis->pol,bl,i);
					for (j=0; j<n[idx]; j++) {
						if (isnan(data[idx][j])) {
							data[idx][j] = vis->data[i];
							break;
						}
					}
				}
				vis = vis->next;
			}
		}

		// Get median and scatter
        	for (i=0; i<2*n_bl*n_chan; i++) meddev_cmplx(data[i],n[i],&(med_spec[i]),&(rms_spec[i]));

		// Compute a channel median for each baseline.
		median = malloc(sizeof(complex float) * 2 * n_bl);
		deviation = malloc(sizeof(complex float) * 2 * n_bl);
		if (!median || !deviation) bug_c('f',"Out of memory in function noncal_stats.");
		meddevspec(n_bl, n_chan, med_spec, median, deviation);

		bin->med_spec = med_spec;
		bin->rms_spec = rms_spec;
		bin->median = median;
		bin->deviation = deviation;

		// Clean up
		for (i=0; i<2*n_bl*n_chan; i++) {
			free(data[i]);	// it's safe to call free(NULL)
		}
		free(data);

		bin = bin->next;
	}
}



void check_phases(dataset_struct *first) {
	bin_struct *bin;
	dataset_struct *visdata;
	unsigned int idx, pol, bl, ch, n_bl, n_chan, nflag;
	float phase_var, var, med;

	n_bl = first->n_bl;
	n_chan = first->n_chan;

	printf("Examining calibrator phase variance:");
	nflag=0;
	visdata = first;
	while (visdata != NULL) {
		bin = visdata->bin;
		while (bin != NULL) {
			for (pol=0; pol<2; pol++)
			for (bl=0; bl<n_bl; bl++) {
				idx = pol*n_bl+bl;
				// Estimate of the variance in phase of this baseline; this is channel-averaged.
				// Essentially this is a measure of 1/SNR using phase.
				var = cabsf(bin->deviation[idx]);
				med = cabsf(bin->median[idx]);
				phase_var = atan2f(var,med);

				if (phase_var > 1.0) {
					nflag++;
					for (ch=0; ch<n_chan; ch++) {
						idx = pol*n_bl*n_chan + bl*n_chan+ch;
						set_bin_flag(bin,pol,bl,ch,1);
					}
				}
			}
			bin = bin->next;
		}
		visdata = visdata->next;
	}
	printf(" flagged %u baseline/pols.\n",nflag);
}





bin_struct *make_bin(vis_struct *vis) {
	bin_struct *bin;
	unsigned i;

	bin = malloc(sizeof(bin_struct));
	if (!bin) bug_c('f',"make_bin: Out of virtual address space.");
	bin->data = vis;
	bin->visdata = vis->visdata;
	bin->first_time=vis->time + bin->visdata->time0;
	bin->last_time=vis->time + bin->visdata->time0;
	bin->next=NULL;
	bin->gains=NULL;
	bin->med_spec = NULL;
	bin->rms_spec = NULL;
	bin->median = NULL;
	bin->deviation = NULL;
	bin->n_vis=1;
	bin->flags = malloc(sizeof(char)*(1+bin->visdata->n_chan*bin->visdata->n_bl/4));
	if (!bin->flags) bug_c('f',"Out of memory in function 'make_bin'");
	for (i=0; i<1+bin->visdata->n_chan*bin->visdata->n_bl/4; i++) bin->flags[i]=0;
	vis->visdata->n_bins++;

	return(bin);
}


void insert_vis(vis_struct *vis, dataset_struct *visdata) {
	bin_struct *bin = visdata->bin;
	vis_struct *tmpvis;

	if (visdata->bin == NULL) {
		visdata->bin = make_bin(vis);
		return;
	}
	while (bin->next) { bin = bin->next; }
	if (vis->time < bin->first_time-bin->visdata->time0) {
		bug_c('f',"Visibilities do not appear to be in time order.");
	}
	if (vis->time + vis->visdata->time0 - bin->last_time > 5 * visdata->int_time / 86400) {
		/* Gap in data; assume a new scan. Make a new bin. */
		bin->next = make_bin(vis);
	}
	else { /* Insert the visibility into this bin's data list */
		tmpvis = bin->data;
		while (tmpvis->next) tmpvis = tmpvis->next;
		tmpvis->next = vis;
		bin->n_vis++;
		visdata->n_vis++;
		if (vis->time > bin->last_time-bin->visdata->time0) {
			bin->last_time = vis->time+bin->visdata->time0;
		}
		if (vis->time < bin->first_time-bin->visdata->time0) {
			bug_c('f',"Error: putting a vis in the wrong bin. Data not sorted in time order?");
		}
	}
}


/*
 * Return value:
 *	>0 : Return number of channels read.
 *	0  : EoF reached, no data read.
 *	-1 : Error reading data.
 */
vis_struct *read_vis(dataset_struct *visdata) {
	vis_struct *vis;
	float data[MAXCHAN*2];
	int flags[MAXCHAN];
	double preamble[4];	// Preamble is float[4], contains u,v,time,baseline
	int j, nread;
	char defpol=0;				// default polarization for uvrdvri_c
	double sigmasq;

	uvread_c(visdata->tvis,preamble,data,flags,MAXCHAN,&nread);
	if (nread == 0) { return(NULL); }		// Exit at end of file
	if (visdata->n_chan == 0) {
		visdata->n_chan = nread;
	}
	else if (visdata->n_chan != nread) {
		fprintf(stderr,"Error: number of channels has changed from %u to %u\n",visdata->n_chan,nread);
		bug_c('f',"Number of channels changed.");
	}

	vis = malloc(sizeof (vis_struct));
	if (!vis) bug_c('f',"Out of virtual address space. Too much data?");
	vis->flags = malloc(1 + visdata->n_chan / 8);
	if (!vis->flags) bug_c('f',"Out of virtual address space. Too much data?");

	// Pack the flags
	for (j=0; j<visdata->n_chan; j++) {
		set_flag(vis,j,flags[j]);
	}

	vis->u = preamble[0];
	vis->v = preamble[1];
	if (visdata->time0 == 0) {
		visdata->time0 = preamble[2];
		vis->time = 0.0;
	}
	else vis->time = (preamble[2] - visdata->time0);
	vis->baseline = preamble[3];
	basanta_(&preamble[3], &(vis->ant[0]), &(vis->ant[1]));
	vis->ant[0]--;		// These are zero-based
	vis->ant[1]--;
	vis->visdata = visdata;
	vis->data = malloc(sizeof(complex float) * visdata->n_chan);
	for (j=0; j<visdata->n_chan; j++) {
		vis->data[j] = data[2*j] + data[2*j+1] * I;
	}

	/* ATA data are 16-bit integers, scaled by mulitplying by variable "tscale".
	   So, to obtain the original 16-bit data, try this:
	     uvread_c() // load data
	     uvrdvr_c() // get tscale
	     short int data = rint(data / tscale)
	*/

	uvrdvr_c(visdata->tvis,H_INT,"pol",&(vis->pol),&defpol,3);
	uvinfo_c(visdata->tvis,"variance",&sigmasq);
	vis->thermal_sigmasq = sigmasq;
	if (vis->thermal_sigmasq <= 0) {
		bug_c('w',"bad value for thermal noise.");
		vis->thermal_sigmasq = 0.0;
	}
	vis->next = NULL;

	return(vis);
}


void write_flags(dataset_struct *visdata) {
	vis_struct *vis;
	bin_struct *bin;
	int flags[visdata->n_chan];
	unsigned int i,ch;
	unsigned long nbefore=0, nafter=0, ntot=0, nflag=0;
	int bl;
	char pol;

	uvrewind_c(visdata->tvis);

	while (1) {
		vis = read_vis(visdata);
		if (vis==NULL) { break; }
		for (ch=0; ch<visdata->n_chan; ch++) flags[ch] = good(vis,ch);

		nbefore += count_unflagged_chan(vis);
		ntot += visdata->n_chan;

		bin = visdata->bin;
		while (bin) {	// Find the bin for this vis. FIXME still inefficient, we shouldn't have to step through every previous bin for every vis.
			if ((vis->time >= bin->first_time-visdata->time0) && (vis->time <= bin->last_time-visdata->time0)) break;
			bin = bin->next;
		}
		if (!bin) {	// Couldn't find a bin
			for (ch=0; ch<visdata->n_chan; ch++) if (flags[ch]) {
				fprintf(stderr,"Error: unflagged data found outside of any scan boundary.\n");
				abort();
			}
			continue;
		}

		else {					// Found a bin corresponding to a scan which contains this visibility
			if (vis->pol == visdata->ppol1) pol=0;
			else if (vis->pol == visdata->ppol2) pol=1;
			else pol=2;		// cross-hand, so flag the vis if either of the pols are flagged in the bin->flag table
			bl = get_bl(vis);
			for (ch=0; ch<visdata->n_chan; ch++) if (flags[ch]) {
				if (pol<2) flags[ch] &= !get_bin_flag(bin, pol, bl, ch);
				else flags[ch] &= !get_bin_flag(bin, 0, bl, ch) && !get_bin_flag(bin, 1, bl, ch);
			}

			// Flag RFI for individual data. Do this here instead of with the other flagging routines since
			// the internal data structures don't have cross-hand pol visibilities.
			if (!norfi || !nodistro) {
				// Apply gains if necessary
				if (!noband && bin->gains && (!norfi || !nodistro)) {
					unsigned int idx1;
					unsigned int idx2;
					idx1 = pol*visdata->n_ants*visdata->n_chan + vis->ant[0] * visdata->n_chan + ch;
					idx2 = pol*visdata->n_ants*visdata->n_chan + vis->ant[1] * visdata->n_chan + ch;
					vis->data[ch] *= bin->gains[idx1] * ~ bin->gains[idx2];
				}
				if (bin->median && bin->deviation) {
					if (pol < 2) for (ch=0; ch<visdata->n_chan; ch++) {
						if (!flags[ch]) continue;	// Don't bother if it is already flagged
						i = pol * visdata->n_bl + bl;
						if (cabsf(vis->data[ch] - bin->median[i]) > 10 * cabsf(bin->deviation[i])) {
							nflag++;
							flags[ch] = 0;
						}
					}
				}
			}
		}

		for (ch=0; ch<visdata->n_chan; ch++) if (flags[ch]) nafter++;
		if (!noflag) uvflgwr_c(visdata->tvis, flags);

		free(vis->data);
		free(vis->flags);
		free(vis);
	}

	if (nflag) printf("Flagged %lu individual visibility channels for RFI.\n",nflag);
	printf("Original data: %lu good correlations of %lu total\n",nbefore,ntot);
	printf("Modified data: %lu good correlations of %lu total\n",nafter,ntot);
	printf("Flagged %lu additional correlations (%.2f%%)\n",nbefore-nafter,(double)(nbefore-nafter)*100.0/nbefore);
	printf("%.2f%% data retention\n\n",100.0*nafter/ntot);
}



// Only the fname field of the visdata parameter need be set in advance
void load_data(dataset_struct *visdata) {
	int i,j;
	vis_struct *vis;
	char obstype[32];
	char first=1;
	char okbase, okpol;
	int n_ants=-1;
	const unsigned int defnants = 0;	// default number of antennas
	const float defitime = -1.0;		// default integration time
	const double defradec = (-3.0*M_PI);	// default RA / DEC
	double obsra=defradec, obsdec=defradec;
	float int_time=defitime;


	visdata->n_bins=0;
	visdata->time0=0.0;
	visdata->n_bad_stokes=0;
	visdata->n_bad=0;
	visdata->n_flagged_vischan=0;
	visdata->n_vis=0;
	visdata->n_ants=0;
	visdata->n_chan=0;
	visdata->ppol1=0;
	visdata->ppol2=0;
	visdata->bin=NULL;
	for (i=0; i<13; i++) { visdata->polpresent[i] = 0; }

	uvopen_c(&visdata->tvis,visdata->fname,"old");
	rdhda_c(visdata->tvis,"obstype",obstype,"crosscorrelation",32);
	printf("\n%s contains %s data.\n",visdata->fname,obstype);

//	if (strncmp(obstype,"cross",5))
//		bug_c('f',"The visibility file does not contain crosscorrelation data.\n");
//
	while (1) {
		vis=read_vis(visdata);

		if (vis==NULL) { break; }					// Exit at end of file

		// ATA data are 16-bit integers, scaled by mulitplying by variable "tscale".
		//   So, to obtain the original 16-bit data, try this:
		//     uvread_c() // load data
		//     uvrdvr_c() // get tscale
		//     short int data = rint(data / tscale)

		visdata->polpresent[vis->pol+8] = 1;
		okpol=polspara_((int *) &(vis->pol));	// Ensure parallel hand only

		uvrdvr_c(visdata->tvis,H_INT,"nants",(char *)&n_ants,(char *)&defnants,5);
		uvrdvr_c(visdata->tvis,H_REAL,"inttime", (char *)&int_time,(char *) &defitime, 7);
		uvrdvr_c(visdata->tvis,H_DBLE,"obsra", (char *)&obsra,(char *)&defradec, 2);
		uvrdvr_c(visdata->tvis,H_DBLE,"obsdec", (char *)&obsdec,(char *)&defradec, 3);

		if (first) {	// Get # of antennas, integration time, RA and DEC -- these should not change.
			visdata->ra = obsra;
			visdata->dec = obsdec;
			visdata->n_ants = n_ants;
			visdata->n_bl = (visdata->n_ants * (visdata->n_ants + 1)) / 2;	// Allow for autocorrelations
			visdata->int_time = int_time;
			first = 0;
		}
		else {	// Make sure # of antennas, integration time, RA and DEC haven't changed
			if (n_ants != visdata->n_ants) {
				fprintf(stderr,"Error: number of antenna has changed from %d to %d\n",visdata->n_ants,n_ants);
				bug_c('f',"Unexpected change to number of antennas.");
			}

			if (int_time != visdata->int_time) {
				fprintf(stderr,"Error: integration time has changed from %f to %f\n",visdata->int_time,int_time);
				fprintf(stderr,"\t\t at time %f\n",vis->time*86400);
				visdata->int_time = int_time;
		//		bug_c('f',"Unexpected change to integration time.");
			}
			if (obsra != visdata->ra) {
		//		fprintf(stderr,"RA changed from: %f to %f\n",visdata->ra,obsra);
		//		bug_c('f',"Unexpected change to RA.");
			}
			if (obsdec != visdata->dec) {
		//		fprintf(stderr,"DEC changed from: %f to %f\n",visdata->dec,obsdec);
		//		bug_c('f',"Unexpected change to DEC.");
			}

		}
		i = count_unflagged_chan(vis);
		okbase=((MIN(vis->ant[0],vis->ant[1]) >= 0) && \
			(MAX(vis->ant[0],vis->ant[1]) < visdata->n_ants));
		if (okbase && okpol && (i > 0)) {
			insert_vis(vis,visdata);
			visdata->n_flagged_vischan += visdata->n_chan - i;
		}
		else {
			if (okpol) visdata->n_bad++;
			else visdata->n_bad_stokes++;
			free(vis->data);
			free(vis->flags);
			free(vis);
		}
	}

	// Now, loop over the polarization list and find the parallel hand polarizations
	j=0;
	for (i=-8; i<5; i++) {
		if (visdata->polpresent[i+8] && polspara_(&i)) {
			j++;
			if (!visdata->ppol1) visdata->ppol1 = i;
			else if (!visdata->ppol2) visdata->ppol2 = i;
			else {
				printf("Error: pol1 = %d  pol2 = %d   also found pol code %d\n",visdata->ppol1,visdata->ppol2,i);
				bug_c('f',"Too many parallel-hand polarizations found!");
			}
		}
	}
	printf("Found %d different parallel-hand polarizations.\n",j);
}


void cleanup(dataset_struct *visdata) {
	bin_struct *bin, *tmpbin;
	vis_struct *vis, *tmpvis;

	bin = visdata->bin;
	while (bin) {						// FIXME valgrind reports Conditional jump or move depends on uninitialised value(s)
		free(bin->flags);
		free(bin->gains);
		free(bin->med_spec);
		free(bin->rms_spec);

		vis=bin->data;
		while(vis) {
			tmpvis=vis;
			vis=vis->next;
			free(tmpvis->data);
			free(tmpvis->flags);
			free(tmpvis);
		}
		tmpbin = bin;
		bin = bin->next;
		free(bin);
	}
	free(visdata);
}


plist list_insert(plist list, bin_struct *bin) {
        plist tmp, loc;
	bin_struct *b;

        tmp = (plist) malloc(sizeof(struct list));
        tmp->data = (void *) bin;

	// First handle the case where the bin is inserted as the first element,
	// either because the list was empty or because we have the earliest time.
	if (list == NULL) {
                tmp->next = NULL;
        	tmp->prev = NULL;
                return (tmp);
        }
	b = (bin_struct *) list->data;
        if (bin->last_time < b->first_time) {
                tmp->next = list;
        	tmp->prev = NULL;
        	list->prev = tmp;
                return (tmp);
        }

	loc = list;
	b = (bin_struct *) loc->data;
	while (loc->next != NULL && bin->first_time > b->last_time) {
		loc = loc->next;
		b = (bin_struct *) loc->data;
	}
	tmp->next = loc->next;
	tmp->prev = loc;
	loc->next = tmp;
        return(tmp);
}


void interpolate_flags(plist binlist, dataset_struct *visdata) {
	bin_struct *bin, *calbin;
	plist l;
	unsigned int i;

	bin = visdata->bin;

	while (bin != NULL) {
		l = binlist;
		calbin = (bin_struct *) l->data;

		// Find the first calibrator scan that occurs after our last time
		while (l->next != NULL && bin->first_time < calbin->last_time) {
			l = l->next;
			calbin = (bin_struct *) l->data;
		}

		if (calbin->last_time < bin->first_time) printf("Warning: the last scan is not a calibrator\n");
		// Apply calibrator flags for this calibrator bin
		for (i=0; i<1+bin->visdata->n_chan*bin->visdata->n_bl/4; i++) bin->flags[i] |= calbin->flags[i];
		// Apply calibrator flags for the previous calibrator bin
		l = l->prev;
		if (l == NULL) printf("Warning: the first scan is not a calibrator\n");
		else {
			calbin = (bin_struct *) l->data;
			for (i=0; i<1+bin->visdata->n_chan*bin->visdata->n_bl/4; i++) bin->flags[i] |= calbin->flags[i];
		}

		bin = bin->next;
	}

}




/* 
 * To provide your own main procedure in place of g77's, make sure you specify
 * the object file defining that procedure before `-lg2c' on the g77 command
 * line. Since the `-lg2c' option is implicitly provided, this is usually
 * straightforward. (Use the `--verbose' option to see how and where g77
 * implicitly adds `-lg2c' in a command line that will link the program. Feel
 * free to specify `-lg2c' explicitly, as appropriate.) 
 *
 * However, when providing your own main, make sure you perform the appropriate
 * tasks in the appropriate order. For example, if your main does not call
 * f_setarg, make sure the rest of your application does not call GETARG
 * or IARGC. 
 *
 * And, if your main fails to ensure that f_exit is called upon program exit,
 * some files might end up incompletely written, some scratch files might be
 * left lying around, and some existing files being written might be left with
 * old data not properly truncated at the end. 
 */


int main(int argc, char *argv[]) {
	char **cmdline;
	char str[4096];
	int i, j; // , n_head=N_HEADER_PARAMS;
//	char doline, line_type[32], buff[80];
//	int n_chan;
//	float line_start, line_width, line_step;
//	float sels[maxsels];
	bin_struct *bin;
	plist binlist;

	f_setarg(argc,argv);
	f_setsig();
	f_init();
	printf("Autoflag\n");

	/* Copy the command line before keyini_ destroys it... */
	cmdline=malloc(sizeof(char *) * (argc + 1));
	for (i=0; i<argc; i++) {
		j = strlen(argv[i]) + 1;
		*(cmdline+i)=malloc(j);								// FIXME memory leak
		strncpy(*(cmdline+i),argv[i],j);
	}

	keyini_();
	keyini_c(argc, argv);

	/* Get the calibrator file names */
	keyf_c("cal",str,&blank);
	while (str[0]) {
		if (firstcaldata == NULL) {
			firstcaldata = malloc(sizeof(dataset_struct));
			visdata = firstcaldata;
		}
		else {
			visdata->next = malloc(sizeof(dataset_struct));				// FIXME memory leak
			visdata = visdata->next;
		}
		if (!visdata) bug_c('f',"Failure in an early malloc() call. Bad.");
		strncpy(visdata->fname,str,4096);
		n_cal_files++;
		keyf_c("cal",str,&blank);
	}

	/* Get the visibility file names */
	keyf_c("vis",str,&blank);
	while (str[0]) {
		if (!firstvisdata) {
			firstvisdata = malloc(sizeof(dataset_struct));
			visdata = firstvisdata;
		}
		else {
			visdata->next = malloc(sizeof(dataset_struct));
			visdata = visdata->next;
		}
		if (!visdata) bug_c('f',"Failure in an early malloc() call. Bad.");
		strncpy(visdata->fname,str,4096);
		n_vis_files++;
		keyf_c("vis",str,&blank);
	}

	if (!n_cal_files) bug_c('f',"No calibrator files.");

//	if (keyprsnt_c("select") || keyprsnt_c("line")) bug_c('w',"flags may be applied to data that were not selected.");
//	selinput_("select",sels,&maxsels,strlen("select"));
//	do keya_c("select",buff,&blank);	// ugly, avoids warning message
//	while (buff[0]);

//	keyline_(line_type,&n_chan,&line_start,&line_width,&line_step,32);
//	doline = (line_type[0] != ' ');
	getopt_dave();
	keyfin_c();

	if (noflag) printf("NOFLAG OPTION SELECTED: FLAGS WILL NOT BE SAVED.\n");
	/* Should verify parameter values */

	/* Read data */

	visdata = firstcaldata;
	while (visdata) {
		printf("Reading visibility data from %s\n",visdata->fname);
//		selapply_(&visdata->tvis, sels, &one);
//		doline = (line_type[0] != ' ');
		load_data(visdata);

		printf("# of scans: %d\n",visdata->n_bins);
		printf("# of accepted records: %lu\n",visdata->n_vis);
		printf("# of completely flagged records: %lu\n",visdata->n_bad);
		printf("# of records rejected due to stokes parameter: %lu\n",visdata->n_bad_stokes);
		printf("mean # of channels flagged as bad: %1.3f\n",(float) visdata->n_flagged_vischan / visdata->n_vis);

		printf("Calculating spectral statistics...\n");
		bin = visdata->bin;
		i=0;
		while (bin) {
			i++;
			printf("\nProcessing scan %d\n",i);
			calflag(bin);
			bin = bin->next;
		}

		if (!nophase) {
			check_phases(firstcaldata);
		}

		if (!noflag) printf("\nWriting flag table for %s\n",visdata->fname);
		write_flags(visdata);

		uvclose_c(visdata->tvis);
		visdata = visdata->next;
	}


	// Make a time-sorted linked list of calibrator bins.
	visdata = firstcaldata;
	i=0;
	while (visdata != NULL) {
		bin = visdata->bin;
		while (bin != NULL && i<15) {
			binlist = list_insert(binlist, bin);
			bin = bin->next;
		}
		visdata = visdata->next;
	}

	/* Process non-calibrator data */
	if (n_vis_files) {
		visdata = firstvisdata;
		while (visdata) {
			printf("Reading visibility data from %s\n",visdata->fname);
//			selapply_(&visdata->tvis, sels, &one);
//			doline = (line_type[0] != ' ');
			load_data(visdata);

			printf("# of scans: %d\n",visdata->n_bins);
			printf("# of accepted records: %lu\n",visdata->n_vis);
			printf("# of completely flagged records: %lu\n",visdata->n_bad);
			printf("# of records rejected due to stokes parameter: %lu\n",visdata->n_bad_stokes);
			printf("mean # of channels flagged as bad: %1.3f\n",(float) visdata->n_flagged_vischan / visdata->n_vis);

			// Copy calibrator flags to our flag table
			interpolate_flags(binlist,visdata);

			noncal_stats(visdata);

			// FIXME: run basic flagging algorithm on these data

			if (!noflag) printf("Writing flag table for %s\n",visdata->fname);
			write_flags(visdata);

			uvclose_c(visdata->tvis);
			visdata = visdata->next;
		}
	}
/*
	// Write some history 
	if (!noflag) {
		snprintf(buff,80,"%s/history",visdata->fname);
		fd = fopen(buff,"a");
		if (!fd) fprintf(stderr,"Error opening history file %s\n",buff);
		fprintf(fd,"autoflag: command line:\n");
		for (j=1; j<argc; j++) fprintf(fd,"autoflag: %s\n",*(cmdline+j));
	

		if (fclose(fd)) fprintf(stderr,"Error closing history file %s\n",buff);
		uvclose_c(visdata->tvis);

*/
/*
	// Clean everything up
	visdata=firstcaldata;
	while (visdata) {
		firstcaldata=visdata;
		visdata=visdata->next;
		cleanup(firstcaldata);
	}
	visdata=firstvisdata;
	while (visdata) {
		firstvisdata=visdata;
		visdata=visdata->next;
		cleanup(firstvisdata);
	}
	free(cmdline);
*/
	f_exit();
	return 0;
}
