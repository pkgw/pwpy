=begin
= PGPLOTのインストール

PGPLOTは configure を使わないのでインストールが若干面倒です。
以下は Solaris、GCC という環境でPGPLOTをコンパイル、
インストールする手順を説明します。
他のOSでもUNIXならほとんど同じようにしてインストールできると思います。
((<本家のインストール説明のページ|URL:http://www.astro.caltech.edu/~tjp/pgplot/install.html>))
もご覧下さい。

=== PGPLOTのソースを用意
((<PGPLOTのサイト|URL:http://www.astro.caltech.edu/~tjp/pgplot/>))
から
((<ソースコード|URL:ftp://ftp.astro.caltech.edu/pub/pgplot/pgplot5.2.tar.gz>))
をダウンロード、展開し、pgplotのディレクトリに移動します。

  gunzip -c pgplot5.2.tar.gz | tar xvf -
  cd pgplot

=== 作業ディレクトリを作成
作業ディレクトリを作ります。ここでは build という名前にします。

  mkdir build
  cd build

=== drivers.listを編集
PGPLOTで描画を出力するドライバを選択します。
drivers.list というファイルをコピーしてエディタで開き、
使いたいドライバの行の頭の ! の文字を削除します。

  cp ../drivers.list .
  vi drivers.list

ドライバはお好みで選択できますが、UNIXなら
PNG, PPM, Postscipt, XWD, XWINDOW, XSERVE, XTERM
あたりを選んでおくのが一般的でしょう。
PNG driverを組み込むには、
((<libpng|URL:http://www.libpng.org/pub/png/png.html>)) が必要です。
他にもたくさんのドライバが含まれていますが、
プリンタドライバの中にはコンパイルの時にエラーが出るものがあったり、
GIFはライセンスに引っ掛かったりします。

=== makefile 作成
次のコマンドで makefile を作成します。
  ../makemake .. sol2 g77_gcc
1番目の引数はソースのあるディレクトリの指定です。
ここではソースディレクトリの下にいるので、((%..%)) を指定します。
2番目の引数はOSの種類で、ソースディレクトリにある
((%sys_*%)) というディレクトリの中の ((%*%)) の部分を指定します。
3番目の引数はコンパイラなどの設定で、sys_* の下にある
((%*.conf%)) というファイルの ((%*%)) の部分を指定します。
もしこの中になければ、最も近そうなやつを選びます。

makefile を作成したら、ざっと見て設定が正しいかチェックします。
ここで、PGPLOT ver 5.2.2 で PNG driverを使う場合、
吐き出された makefile は、

  pndriv.o : ./png.h ./pngconf.h ./zlib.h ./zconf.h

というまずい設定になっているので、この行を削除します。

=== コンパイル
makefile を編集したら、ライブラリをコンパイルします。

  make
  make cpg

=== インストール
make install が用意されていないので、手動でコピーします。
必要なら root になってください。
まずインストール先のディレクトリを環境変数にセットします。
csh系なら、

  setenv PREFIX  /usr/local
  setenv PGPLOT_DIR  ${PREFIX}/pgplot

インストール先は自由に選べますが、
コンパイル時にパス指定が必要になるかもしれません。
次に必要なファイルをコピーします。

  cp -p libpgplot.a libpgplot.so* libcpgplot.a ${PREFIX}/lib
  cp -p cpgplot.h ${PREFIX}/include
  mkdir ${PGPLOT_DIR}
  cp -p grfont.dat rgb.txt pgxwin_server ${PGPLOT_DIR}

これでインストール終了です。

=== デモの実行
コンパイルがうまくいったかどうかデモプログラムを走らせてみましょう。
コンパイルしたディレクトリに pgdemo1 から pgdemo17 までと cpgdemo
という実行ファイルができているはずです。それらを実行できれば正しく
コンパイルされているはずです。

=== ユーザ設定
PGPLOTを使うユーザは、環境変数へ次の設定しておくとよいでしょう。
  setenv PGPLOT_DIR  /usr/local/pgplot
  setenv PGPLOT_DEV  /xwin
PGPLOT_DIR は上でインストールしたディレクトリと同じ、
PGPLOT_DEV はデフォルトのデバイスです。
その他の環境変数は特に設定しなくてもいいと思いますが、詳しくは
((<ここ|URL:http://www.astro.caltech.edu/~tjp/pgplot/chapter1.html#ENV>))
をご覧下さい。

<<< trailer

=end
