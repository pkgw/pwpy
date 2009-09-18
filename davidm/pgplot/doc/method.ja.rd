=begin
= module Pgplot

== モジュールメソッド

=== 操作
--- pgopen([device])
PGPLOTセッションを開始する。戻り値としてステータスを返す。

--- pgbeg([device, [nxsub, [nysub]]])
(obsolete)
PGPLOTセッションを開始する。戻り値としてステータスを返す。

--- pgask( [true|false] )

--- pgenv( xmin,xmax,ymin,ymax [,just, axis] )

=== 線・マーカの描画
--- pgline( xarray, yarray )
xarray, yarray を結ぶ線を描く。
xarray, yarray はそれぞれ X, Y 座標の配列。

--- pgpt( xarray, yarray [,symbol] )
xarray, yarray の位置に、symbol のマーカを描く。

--- pgpnts( xarray, yarray, symarray )
xarray, yarray の位置に、対応する symarray のマーカをそれぞれ描く。

=== ヒストグラム
--- pgbin( xarray, yarray [,center] )

--- pghist( data, nbin [,range, flag] )

=== エラーバー
--- pgerrb( dir, x, y, err [,tlen] )
エラーバーを描く。
tlen に端点に描くバーの長さを指定。
+ 片側エラーバー:
 * dir = 1 for +X (X to X+err)
 * dir = 2 for +Y (Y to Y+err)
 * dir = 3 for -X (X to X-err)
 * dir = 4 for -Y (Y to Y-err)
+ 両側エラーバー:
 * dir = 5 for +/-X (X-err to X+err)
 * dir = 6 for +/-Y (Y-err to Y+err)

--- pgerrx( x1, x2, y [,tlen] )
x1 から x2 までを結ぶエラーバーを描く。
tlen に端点に描くバーの長さを指定。

--- pgerry( x, y1, y2 [,tlen] )
y1 から y2 までを結ぶエラーバーを描く。
tlen に端点に描くバーの長さを指定。

=== 等高線
--- pgcont( map, cont [,tr] )
map で与えた２次元マップの等高線を描く。
cont には等高線のレベルまたはその配列を与える。

--- pgcons( map, cont [,tr] )
PGCONTより速いアルゴルズムで描くんだそうな。

--- pgconb( map, cont [,blank, tr] )
blankで与えた値を欠損値として等高線を描く。

--- pgconf( map, cont_range [,tr] )
cont_range に Rangeクラスオブジェクトで与えた範囲のレベルを塗り潰す。

--- pgconl( map, cont, label [,intval, minint, tr] )
等高線にラベルをつける。

=== 画像
--- pgimag( array [,range, tr] )
カラースケールで array (２次元配列) の画像を描く。

--- pgctab( l, r,g,b [,contra,bright] )
pgimag で使用するカラーテーブルを設定する。

--- pggray( array [,range, tr] )
グレースケールで array (２次元配列) の画像を描く。

--- pgpixl( array [,x1,x2,y1,y2] )
array (２次元配列) の画像を、長方形のpixel 1つ1つで描く。

--- pgvect( x, y [,scale, pos, tr, blank] )
ベクトル場を描く。

=== 座標軸の描画
--- pgtick( x1, y1, x2, y2, v, [str], {"tickl", "tickr", "disp", "orient"} )

--- pgaxis( x1, y1, x2, y2, v1, v2,
         {"opt", "step", "nsub", "tickl", "tickr", "frac", "disp", "orient"} )

=== カーソル入力
--- pgcurs([x,y])
クリックまたはキータイプのイベントを取得する。
x,y を指定すると始めにその位置にカーソルを移動する。
イベントを取得すると
カーソル位置(WC)と文字を PgCursorクラスのインスタンスで返す。

--- pgband( mode, [ xref, yref, [x, y, [posn]]])
クリックまたはキータイプのイベントを取得する。
x,y を指定すると始めにその位置にカーソルを移動する。
xref, yref はアンカー点の位置(後述)で、省略すると現在位置となる。
イベントを取得すると
カーソル位置(WC)と文字を PgCursorクラスのインスタンスで返す。
modeによりカーソル入力中の描画方法を指定できる。
 * mode=0 : 描画なし。
 * mode=1 : アンカー点とカーソルを結ぶ線。
 * mode=2 : アンカー点とカーソルを対角とする長方形。
 * mode=3 : アンカー点とカーソル位置それぞれを通る２本の水平線。
 * mode=4 : アンカー点とカーソル位置それぞれを通る２本の垂直線。
 * mode=5 : カーソル位置を通る水平線。
 * mode=6 : カーソル位置を通る垂直線。
 * mode=7 : カーソル位置を通る十字線。

--- pgolin( x, y, [sym, [npt]] )
マウスカーソルで座標を連続して入力する。
x,y にはあらかじめ NArray::SFLOAT 型の配列を与えておき、
そこへクリックした順番に座標を記録していく。
入力できる個数はこの配列のサイズで制限される。
カーソルで入力した点は、マーカ sym で描画される。
npt を指定すると、あらかじめ npt 個の点が入力されているとみなす。
戻り値は入力した点の数。

--- pgncur( x, y, [sym, [npt]] )
x,yに記録される順番が x の小さい順であることを除き、pgolin と同じ。

--- pglcur( x, y, [npt] )
入力した点を結ぶ線が描かれることを除いて、pgolin と同じ。

=== ステータスを返す
--- pgqinf(item)
  value = pgqinf(item)

--- pgqdt([ndev])
  type, descr, inter = pgqdt([ndev])


=end
