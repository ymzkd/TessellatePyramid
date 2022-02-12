# Tessellate Pyramid
平面多角形と1頂点を結んだ多角錐の分割を取り扱う。


Pythonで幾何学計算を行い、HopsコンポーネントとPythonのウェブアプリケーションフレームワークであるFlaskを使ってRhino+GHで幾何学データを入出力を行う。必要なパッケージは以下のコマンドでインストール。

```
pip install -r requirements.txt
```

Flaskのアプリを起動

```
python app.py
```

HopsコンポーネントのMenuのPathからURLを入力

![menu](/image/menu.png)

URLは`"APP_URL/tessellate"`となる。`APP_URL`はFlaskアプリ起動時のログを参照

![input](/image/input.png)

## Reference
- [Hops Component with Grasshopper](https://developer.rhino3d.com/guides/compute/hops-component/)
- [scipy.spatial.Delaunay — SciPy v1.8.0 Manual](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.Delaunay.html)