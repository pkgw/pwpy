# Functions from bug.c

require 'dl'

module Mirdl

  BUGSEV = {
    'i' => 'Informational', 'I' => 'Informational',
    'w' => 'Warning',       'W' => 'Warning',
    'e' => 'Error',         'E' => 'Error',
    'f' => 'Fatal',         'F' => 'Fatal'
  }

  BUGSEV_INFO  = 'i'
  BUGSEV_WARN  = 'w'
  BUGSEV_ERROR = 'e'
  BUGSEV_FATAL = 'f'

  BUGLABEL = '(NOT SET)'

  # void bug_c(char s,Const char *m)
  SYM[:bug] = LIBMIR_UVIO['bug_c', '0CS']
  def bug(sev, msg)
    SYM[:bug][sev, msg]
  end
  module_function :bug

  # void buglabel_c(char s,Const char *m)
  SYM[:buglabel] = LIBMIR_UVIO['buglabel_c', '0S']
  def buglabel(name)
    SYM[:buglabel][name]
    BUGLABEL[0..-1] = name
  end
  module_function :buglabel
  # Set bug label
  buglabel(File.basename($0))

  # char *bugmessage_c()
  SYM[:bugmessage] = LIBMIR_UVIO['bugmessage_c', 'S']
  def bugmessage
    r, rs = SYM[:bugmessage][]
    r
  end
  module_function :bugmessage

  # char bugseverity_c()
  SYM[:bugseverity] = LIBMIR_UVIO['bugseverity_c', 'C']
  def bugseverity
    r, rs = SYM[:bugseverity][]
    r.chr
  end
  module_function :bugseverity

  # void bugrecover_c(void (*cl)())
  SYM[:bugrecover] = LIBMIR_UVIO['bugrecover_c', '0P']

  # Define bug-handling callback
  SYM[:bugcallback] = DL.define_callback('0') do
    # Do not raise exception on non-error bugs
    msg = "### #{BUGSEV[bugseverity]} [#{BUGLABEL}]:  #{bugmessage}"
    case bugseverity
    when /[iw]/i: STDERR.puts(msg)
    else raise RuntimeError.new(msg)
    end
  end

  # Install bug-handling callback
  SYM[:bugrecover][SYM[:bugcallback]]
  # TODO Allow user to supply bug handling code
end
