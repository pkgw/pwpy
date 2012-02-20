package jmir.miriad;

import java.text.DecimalFormat;
import java.io.*;

/**
 * Sums all baselines for each moment in time and writes out the
 * "central beam" value as a function of time; data must be precalibrated.
 * Created 1/9/10, derived from UVCopy
 * @author G. R. Harp
 * Change Log:
 */
public class UVExtractCentralBeam
{
	// the input / output filenames
	String mIFile;
	String mOFile;

	// the input/output files
	UVIO mInput = null;
	PrintStream mOutput = null;

	/**
	 * A Miriad program that extracts and writes out the central beam
	 * from a UV file. Input
	 * parameters include:<br>
	 * vis=filename -- required, the input filename<br>
	 * out=filename -- required, the output filename<br>
	 * @param cmd_line command line parameters
	 **/
	public static void main(String[] cmd_line)
	{
		try
		{
			new UVExtractCentralBeam(cmd_line);
		}
		catch (Exception ex)
		{
			ex.printStackTrace();
		}

		// good idea to finalize after a miriad program
		// to close any files inadvertantly left open
		System.runFinalization();
	}

	private UVExtractCentralBeam(String[] cmd_line) throws Exception
	{
		// command line parameters
		Key parms = new Key(cmd_line);
		mIFile = parms.keyf("vis", "***");
		if (mIFile.equals("***"))
			throw new IllegalArgumentException(
				"Must specify input filename (e.g. vis=3c273)");
		String ofile = parms.keyf("out", "***");
		if (ofile.equals("***"))
			throw new IllegalArgumentException(
				"Must specify output filename (e.g. out=3c273.dat)");
		parms.keyfin();
		System.out.println("Opening " + mIFile + ".");

		// open files
		mInput = new UVIO();
		mInput.uvopen(mIFile, "old");
		DecimalFormat df = new DecimalFormat("#0.000000000");
		File out_file = new File(ofile);
		PrintStream mOutput = new PrintStream(new FileOutputStream(out_file));

		// we want baseline coordinates in UVW format
		mInput.uvset("preamble", "uvw/time/baseline", 0, 0.0f, 0.0f, 0.0f);

		// read all names in variable table
		String[] varnames = mInput.listVars();

		// track all the variables
		UVVarTracker vt = new UVVarTracker(mInput);
		for (int i = 0; i < varnames.length; ++i) vt.trackVar(varnames[i]);

		// read in first visibility with slow version of uvread
		// that creates new Visibility objects of just the right size
		Visibility svis = mInput.uvread();
		if (svis == null) throw new Exception("No visibilities in file.");

		// loop over visibilities until done
		double oldtime = svis.preamble[3];;
		double avgr = 0;
		double avgi = 0;
		int numbase = 0;
		for (;;)
		{
			// if we are at the beginning of a new integration, then
			// print out data to file
			double newtime = svis.preamble[3];
			if (newtime > oldtime)
			{
				avgr /= numbase;
				avgi /= numbase;
				// the image must be real valued -- each baseline value
				// has a twin with same real and negative imaginary value
				// Thus only real part is meaningful.
				double beam_avg = avgr;
				mOutput.println("" + df.format(oldtime)
					+ "\t" + df.format(beam_avg));
				avgr = 0;
				avgi = 0;
				numbase = 0;
				oldtime = newtime;
			}

			// sum the unflagged correlations
			double sumr = 0;
			double sumi = 0;
			int num_good = 0;
			for (int i = 0; i < svis.flags.length; ++i)
			{
				// strange as it may seem, unflagged data have a flagval=1
				if (svis.flags[i] == 1)
				{
					sumr += svis.corrs[2*i];
					sumi += svis.corrs[2*i + 1];
					++num_good;
				}
			}

			// store result from baseline in the beam average variables
			if (num_good > 0)
			{
				avgr += sumr / num_good;
				avgi += sumi / num_good;
				++numbase;
			}

			// read in next visibility with the fast version of uvread
			// that recycles the visibility structure
			svis = mInput.uvread(svis);

			// are we at EOF?
			if (svis==null) break;
		}

		// If you don't close the output file before quitting, it will be corrupted
		mInput.uvclose();
		mOutput.close();
		System.out.println("Done.");
	}
}
