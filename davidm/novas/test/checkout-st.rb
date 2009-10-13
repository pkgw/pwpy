#!/usr/bin/env ruby

require 'novas'
require 'test/unit'

include Novas

# Based on checkout-st.c
class NovasTest < Test::Unit::TestCase

  # 'deltat' is the difference in time scales, TT - UT1.
  DELTAT = 60.0

  # The array 'tjd' contains four selected Julian dates at which the
  # star positions will be evaluated.
  TJDS = [2450203.5, 2450203.5, 2450417.5, 2450300.5]

  # FK5 catalog data for three selected stars.
  STARS = [
    CatEntry.new( 2.5301955556, 89.2640888889, "POLARIS",   0,"FK5", 19.8770, -1.520,  0.0070, -17.0),
    CatEntry.new( 5.5334438889, -0.2991333333,  "Delta ORI", 1,"FK5", 0.0100, -0.220,  0.0140,  16.0),
    CatEntry.new( 10.7159355556,-64.3944666667, "Theta CAR", 2,"FK5", -0.3480,  1.000,  0.0000,  24.0),
  ]

  # The observer's terrestrial coordinates (latitude, longitude, height).
  GEO_LOC = Site.new(45.0, -75.0, 0.0, 10.0, 1010.0)

  # The answers (from checkout-st.no)
  TOPO_STAR = [
    [
      "JD = 2450203.500000  Star = POLARIS    RA =  2.446916265  Dec =  89.24633852",
      "JD = 2450203.500000  Star = Delta ORI  RA =  5.530109345  Dec =  -0.30575219",
      "JD = 2450203.500000  Star = Theta CAR  RA = 10.714516141  Dec = -64.38132162"
    ],
    [
      "JD = 2450203.500000  Star = POLARIS    RA =  2.446916265  Dec =  89.24633852",
      "JD = 2450203.500000  Star = Delta ORI  RA =  5.530109345  Dec =  -0.30575219",
      "JD = 2450203.500000  Star = Theta CAR  RA = 10.714516141  Dec = -64.38132162"
    ],
    [
      "JD = 2450417.500000  Star = POLARIS    RA =  2.509407657  Dec =  89.25195435",
      "JD = 2450417.500000  Star = Delta ORI  RA =  5.531194826  Dec =  -0.30305771",
      "JD = 2450417.500000  Star = Theta CAR  RA = 10.714434953  Dec = -64.37368326"
    ],
    [
      "JD = 2450300.500000  Star = POLARIS    RA =  2.481107884  Dec =  89.24253162",
      "JD = 2450300.500000  Star = Delta ORI  RA =  5.530371408  Dec =  -0.30235140",
      "JD = 2450300.500000  Star = Theta CAR  RA = 10.713566017  Dec = -64.37969000"
    ]
  ]

  def test_topo_star
    TJDS.each_index do |tjd_idx|
      tjd = TJDS[tjd_idx]
      STARS.each_index do |star_idx|
        begin
          star = STARS[star_idx]
          ra, dec = star.topo_star(tjd, DELTAT, GEO_LOC)
          got = "JD = %f  Star = %-9s  RA = %12.9f  Dec = %12.8f" %
              [tjd, star.starname, ra, dec]
          assert_equal(TOPO_STAR[tjd_idx][star_idx], got)
        rescue StandardError => e
          puts "%s.  Star %s,  Time %f" % [e, star.starname, tjd]
          raise
        end
      end
    end
  end
end
