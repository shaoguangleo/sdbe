#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  cross_corr.py
#  Apr 08, 2015 11:46:01 HST
#  Copyright 2015
#         
#  Andre Young <andre.young@cfa.harvard.edu>
#  Harvard-Smithsonian Center for Astrophysics
#  60 Garden Street, Cambridge
#  MA 02138
#  
#  Changelog:
#  	AY: Created 2015-04-08

"""
Define utilities for cross-correlation.
"""

from numpy import concatenate, zeros, flipud, sqrt, floor, log2, float64, complex64
from numpy.fft import irfft, fft

def corr_Xt(X0,X1,fft_window_size=32768):
	"""
	Frequency-domain cross-correlation from given spectrum data.
	
	Arguments:
	----------
	X0,X1 -- Spectral snapshots of signals to cross-correlate.
	fft_window_size -- Number of time-domain samples in FFT window.
	
	Returns:
	--------
	s_0x1 -- Time-domain cross-correlation of two signals.
	S_0x1 -- Cross-power spectrum of two signals.
	
	Notes:
	If X0,X1 are two-dimensional averaging over the zeroth dimension is
	done.
	
	X0,X1 are assumed to contain only positive-frequency half-spectra.
	"""
	
	# auto-corr X0,X0
	if (len(X0.shape) == 1):
		S_0x0 = X0 * X0.conjugate()
	else:
		S_0x0 = (X0 * X0.conjugate()).mean(axis=0)
	s_0x0 = irfft(S_0x0,n=fft_window_size).real
	# auto-corr X1,X1
	if (len(X1.shape) == 1):
		S_1x1 = X1 * X1.conjugate()
	else:
		S_1x1 = (X1 * X1.conjugate()).mean(axis=0)
	s_1x1 = irfft(S_1x1,n=fft_window_size).real
	# cross-corr X0,X1
	if ((len(X0.shape) == 1) and (len(X1.shape) == 1)):
		S_0x1 = X0 * X1.conjugate()
	else:
		S_0x1 = (X0 * X1.conjugate()).mean(axis=0)
	s_0x1 = irfft(S_0x1,n=fft_window_size).real/sqrt(s_0x0.max() * s_1x1.max())

	return s_0x1,S_0x1
	
def corr_Xt_search(X0,X1,fft_window_size=32768,search_range=None,search_avg=1):
	"""
	Do FFT-window cross-correlation search on given spectral snapshots.
	
	Arguments:
	----------
	X0,X1 -- Spectral snapshots of signals to cross-correlate.
	fft_window_size -- Number of time-domain samples in FFT window.
	search_range -- Range of FFT window offsets to search for cross-
	correlation, or None to not do search (default is None).
	search_avg -- Number of windows over which to average when doing a
	search. If search is not performed this parameter has no impact
	(default is 1).

	Returns:
	--------
	s_0x1 -- Time-domain cross-correlation of two signals. If search is
	done this is two-dimensional, with relative window offset along the
	zeroth dimension.
	S_0x1 -- Cross-power spectrum of two signals. If search is done
	this is two-dimensional, with relative window offset along the 
	zeroth dimension.
	s_peaks -- If search is done, this returns the peak in the cross-
	correlation as a function of relative window offset.
	
	Notes:
	------
	The search is done from the center window in X0, and over the search
	range, relative to that window, in X1.

	X0,X1 are assumed to contain only positive-frequency half-spectra.
	"""
	
	snapshots_center = X0.shape[0]/2 - search_avg/2
	#~ print "snapshots_center = %d" % snapshots_center
	if (search_range == None):
		search_range = zeros(1)
	
	s_peaks = zeros(len(search_range))
	s_0x1 = zeros([len(search_range),fft_window_size],dtype=float64)
	S_0x1 = zeros([len(search_range),fft_window_size/2],dtype=complex64)
	ii = 0
	for iwindow in search_range:
		#~ print "X0(%d,%d) and X1(%d,%d)" % (snapshots_center,snapshots_center+search_avg,snapshots_center+iwindow,snapshots_center+iwindow+search_avg)
		s_0x1[ii,:],S_0x1[ii,:] = corr_Xt(X0[(snapshots_center):(snapshots_center+search_avg),:],X1[(snapshots_center+iwindow):(snapshots_center+iwindow+search_avg),:],fft_window_size=fft_window_size)
		s_peaks[ii] = s_0x1[ii,:].max()
		ii += 1
	
	return s_0x1,S_0x1,s_peaks

def corr_FXt(x0,x1,fft_window_size=32768,search_range=None,search_avg=1):
	"""
	Do FX cross-correlation by subdividing time-series into FFT windows.
	
	Optionally perform a search over multiple FFT window offsets.
	
	Arguments:
	----------
	x0,x1 -- Time-domain signals.
	fft_window_size -- The number of samples to take in an FFT window.
	search_range -- Range of FFT window offsets to search for cross-
	correlation, or None to not do search (default is None).
	search_avg -- Number of windows over which to average when doing a
	search. If search is not performed this parameter has no impact
	(default is 1).
	
	Returns:
	--------
	s_0x1 -- Time-domain cross-correlation of two signals. If search is
	done this is two-dimensional, with relative window offset along the
	zeroth dimension.
	S_0x1 -- Cross-power spectrum of two signals. If search is done
	this is two-dimensional, with relative window offset along the 
	zeroth dimension.
	s_peaks -- If search is done, this returns the peak in the cross-
	correlation as a function of relative window offset.
	
	Notes:
	------
	The search is done from the center window in x0, and over the search
	range, relative to that window, in x1.
	"""
	
	N_samples = min((2**int(floor(log2(x0.size))),2**int(floor(log2(x1.size)))))
	X0 = fft(x0[:N_samples].reshape((N_samples/fft_window_size,fft_window_size)),axis=1)[:,:fft_window_size/2]
	X1 = fft(x1[:N_samples].reshape((N_samples/fft_window_size,fft_window_size)),axis=1)[:,:fft_window_size/2]
	
	if (search_range == None):
		s_peaks = None
		s_0x1,S_0x1 = corr_Xt(X0,X1,fft_window_size=fft_window_size)
	else:
		# do search
		s_0x1,S_0x1,s_peaks = corr_Xt_search(X0,X1,fft_window_size=fft_window_size,search_range=search_range,search_avg=search_avg)
	
	return s_0x1,S_0x1,s_peaks

