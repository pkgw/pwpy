#ARGF.each do |line|
gsub!(/name="(.+?)"/, %Q[name="#{$1.upcase}"]) if $_=~/^<h3><a name=".+?".*?><em>(pg\w+?)<\/em>/
#  end
#  print line
#end
