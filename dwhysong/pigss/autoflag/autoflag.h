/*
 *	Structures for autoflag.c
 *	David Whysong 2010
 */

typedef struct vis_struct {
        float u, v;
	float time;
	complex float *data;
	float thermal_sigmasq;
	struct vis_struct *next;
	unsigned int baseline;
	unsigned char *flags;
	unsigned short int ant[2];
	char pol;
	struct dataset_struct *visdata;
} vis_struct;

typedef struct bin_struct {
	struct bin_struct *next;
	struct dataset_struct *visdata;
	struct vis_struct *data;
	unsigned long n_vis;
	double first_time, last_time;
	complex float *med_spec, *rms_spec, *gains, *median, *deviation;
	unsigned char *flags;
} bin_struct;

typedef struct dataset_struct {
	struct dataset_struct *next;
	struct bin_struct *bin;
	int tvis;
	unsigned int n_ants, n_chan, n_bl, n_bins;
	unsigned long n_vis, n_bad, n_bad_stokes, n_flagged_vischan;
	double time0, ra, dec;
	float int_time;
	char polpresent[13];
	char ppol1, ppol2;
	char fname[4096];
} dataset_struct;
