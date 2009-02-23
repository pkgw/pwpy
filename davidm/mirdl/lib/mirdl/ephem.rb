# Subroutines and functions from ephem.for

require 'dl'

module Mirdl

  #subroutine Jul2UT(jday,ut)
  SYM[:jul2ut] = LIBMIR['jul2ut_', '0dd']
  def jul2ut(jd)
    r, rs = SYM[:jul2ut][jd.to_f, 0.0]
    rs[1]
  end
  module_function :jul2ut

  #subroutine prerotat(jday,ra,dec,jout,theta)
  SYM[:prerotat] = LIBMIR['prerotat_', '0ddddd']
  def prerotat(jd_in, ra, dec, jd_out)
    r, rs = SYM[:prerotat][jd_in.to_f, ra.to_f, dec.to_f, jd_out.to_f, 0.0]
    rs[4]
  end
  module_function :prerotat

  #subroutine precess(jday1,ra1,dec1,jday2,ra2,dec2)
  SYM[:precess] = LIBMIR['precess_', '0dddddd']
  def precess(jd1, ra1, dec1, jd2)
    r, rs = SYM[:precess][jd1.to_f, ra1.to_f, dec1.to_f, jd2.to_f, 0.0, 0.0]
    rs[4,2]
  end
  module_function :precess

  #subroutine azel(obsra,obsdec,lst,latitude,az,el)
  SYM[:azel] = LIBMIR['azel_', '0dddddd']
  def azel(obsra, obsdec, lst, latitude)
    r, rs = SYM[:azel][obsra.to_f, obsdec.to_f, lst.to_f, latitude.to_f, 0.0, 0.0]
    rs[4,2]
  end
  module_function :azel

  #subroutine parang(obsra,obsdec,lst,latitude,chi)
  SYM[:parang] = LIBMIR['parang_', '0ddddd']
  def parang(obsra, obsdec, lst, latitude)
    r, rs = SYM[:parang][obsra.to_f, obsdec.to_f, lst.to_f, latitude.to_f, 0.0]
    rs[4]
  end
  module_function :parang

  #subroutine Jullst(jday,long,lst)
  SYM[:jullst] = LIBMIR['jullst_', '0ddd']
  def jullst(jd, longitude)
    r, rs = SYM[:jullst][jd.to_f, longitude.to_f, 0.0]
    rs[2]
  end
  module_function :jullst

  #subroutine xyz2llh(x,y,z,lat,long,height)
  SYM[:xyz2llh] = LIBMIR['xyz2llh_', '0dddddd']
  def xyz2llh(x, y, z)
    r, rs = SYM[:xyz2llh][x.to_f, y.to_f, z.to_f, 0.0, 0.0, 0.0]
    rs[3,3]
  end
  module_function :xyz2llh

  #subroutine llh2xyz(lat,long,height,x,y,z)
  SYM[:llh2xyz] = LIBMIR['llh2xyz_', '0dddddd']
  def llh2xyz(lat, longitude, height)
    r, rs = SYM[:llh2xyz][lat.to_f, longitude.to_f, height.to_f, 0.0, 0.0, 0.0]
    rs[3,3]
  end
  module_function :llh2xyz

  #subroutine sph2lmn(ra,dec,lmn)
  SYM[:sph2lmn] = LIBMIR['sph2lmn_', '0ddp'+'I']
  def sph2lmn(ra, dec)
    p = DL.malloc(3*DL.sizeof('D'))
    r, rs = SYM[:sph2lmn][ra.to_f, dec.to_f, p, 3]
    rs[2].to_s(p.size).unpack('D3')
  end
  module_function :sph2lmn

  #subroutine lmn2sph(lmn,ra,dec)
  SYM[:lmn2sph] = LIBMIR['lmn2sph_', '0pdd'+'I']
  def lmn2sph(*lmn)
    lmn = lmn[0] if Array === lmn[0]
    s = lmn.pack('D3')
    r, rs = SYM[:lmn2sph][s, 0.0, 0.0, 3]
    rs[1,2]
  end
  module_function :lmn2sph

  #double precision function epo2jul(epoch,code)
  SYM[:epo2jul] = LIBMIR['epo2jul_', 'DdS'+'I']
  def epo2jul(epoch, code=' ')
    r, rs = SYM[:epo2jul][epoch.to_f, code.to_s[0,1], 1]
    r
  end
  module_function :epo2jul

  #double precision function jul2epo(jday,code)
  SYM[:jul2epo] = LIBMIR['jul2epo_', 'DdS'+'I']
  def jul2epo(jd, code=' ')
    r, rs = SYM[:jul2epo][jd.to_f, code.to_s[0,1], 1]
    r
  end
  module_function :jul2epo

  #double precision function deltime(jday,sys)
  SYM[:deltime] = LIBMIR['deltime_', 'DdS'+'I']
  def deltime(jd_utc,sys)
    sys = sys.to_s
    r, rs = SYM[:deltime][jd_utc.to_f, sys, sys.length]
    r
  end
  module_function :deltime

  #subroutine aberrate(jday,ra,dec,rapp,dapp)
  SYM[:aberrate] = LIBMIR['aberrate_', '0ddddd']
  def aberrate(jd, ra, dec)
    r, rs = SYM[:aberrate][jd.to_f, ra.to_f, dec.to_f, 0.0, 0.0]
    rs[3,2]
  end
  module_function :aberrate

  #double precision function eqeq(jday)
  SYM[:eqeq] = LIBMIR['eqeq_', 'Dd']
  def eqeq(jd)
    r, rs = SYM[:eqeq][jd.to_f]
    r
  end
  module_function :eqeq

  #double precision function mobliq(jday)
  SYM[:mobliq] = LIBMIR['mobliq_', 'Dd']
  def mobliq(jd)
    r, rs = SYM[:mobliq][jd.to_f]
    r
  end
  module_function :mobliq

  #subroutine Nutate(jday,rmean,dmean,rtrue,dtrue)
  SYM[:nutate] = LIBMIR['nutate_', '0ddddd']
  def nutate(jd, ra_mean, dec_mean)
    r, rs = SYM[:nutate][jd.to_f, ra_mean.to_f, dec_mean.to_f, 0.0, 0.0]
    rs[3,2]
  end
  module_function :nutate

  #subroutine nuts(jday,dpsi,deps)
  SYM[:nuts] = LIBMIR['nuts_', '0ddd']
  def nuts(jd)
    r, rs = SYM[:nuts][jd.to_f, 0.0, 0.0]
    rs[1,2]
  end
  module_function :nuts

  #subroutine sunradec(jday,ra,dec)
  SYM[:sunradec] = LIBMIR['sunradec_', '0ddd']
  def sunradec(jd)
    r, rs = SYM[:sunradec][jd.to_f, 0.0, 0.0]
    rs[1,2]
  end
  module_function :sunradec

  #subroutine veccross(x,y,z)
  SYM[:veccross] = LIBMIR['veccross_', '0ppp']
  def veccross(v1, v2)
    s1 = v1.pack('D3')
    s2 = v2.pack('D3')
    p = DL.malloc(3*DL.sizeof('D'))
    r, rs = SYM[:veccross][s1, s2, p]
    rs[2].to_s(p.size).unpack('D3')
  end
  module_function :veccross

  #double precision function LstJul(lst,jday,long)
  SYM[:lstjul] = LIBMIR['lstjul_', 'Dddd']
  def lstjul(lst, jd, longitude)
    r, rs = SYM[:lstjul][lst.to_f, jd.to_f, longitude.to_f]
    r
  end
  module_function :lstjul

  #SUBROUTINE FK45Z (R1950,D1950,JDAY,R2000,D2000)
  SYM[:fk45z] = LIBMIR['fk45z_', '0ddddd']
  def fk45z(ra1950, dec1950, jd=epo2jul(1950.0, 'B'))
    r, rs = SYM[:fk45z][ra1950.to_f, dec1950.to_f, jd.to_f, 0.0, 0.0]
    rs[3,2]
  end
  module_function :fk45z

  #SUBROUTINE FK54Z (R2000,D2000,JDAY,R1950,D1950,DR1950,DD1950)
  SYM[:fk54z] = LIBMIR['fk54z_', '0ddddddd']
  def fk54z(ra2000, dec2000, jd=epo2jul(1950.0,'B'))
    r, rs = SYM[:fk54z][ra2000.to_f, dec2000.to_f, jd.to_f, 0.0, 0.0, 0.0, 0.0]
    rs[3,4]
  end
  module_function :fk54z

  #SUBROUTINE FK524 (R2000,D2000,DR2000,DD2000,P2000,V2000,
  #   :              R1950,D1950,DR1950,DD1950,P1950,V1950)
  SYM[:fk524] = LIBMIR['fk524_', '0dddddddddddd']
  def fk524(ra2000, dec2000, dra2000, ddec2000, px2000, rv2000)
    r, rs = SYM[:fk524][ra2000.to_f, dec2000.to_f, dra2000.to_f,
                        ddec2000.to_f, px2000.to_f, rv2000.to_f,
                        0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    rs[6,6]
  end
  module_function :fk524

  #SUBROUTINE PM (R0, D0, PR, PD, PX, RV, JEP0, JEP1, R1, D1)
  SYM[:pm] = LIBMIR['pm_', '0dddddddddd']
  def pm(ra, dec, pm_ra, pm_dec, px, rv, jep0, jep1)
    r, rs = SYM[:pm][ra.to_f, dec.to_f, pm_ra.to_f, pm_dec.to_f,
                     px.to_f, rv.to_f, jep0.to_f, jep1.to_f, 0.0, 0.0]
    rs[8,2]
  end
  module_function :pm
end
