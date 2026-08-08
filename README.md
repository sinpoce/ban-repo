# sinpoce-repo

这是一个适合个人使用的静态 iOS 越狱软件源模板，兼容 Sileo、Zebra 和 Cydia 的 APT 仓库格式。

仓库内已附带一个无害的 `ban-repo-test` 测试包。它只安装一个文本文件，不提供任何破解或内购绕过功能。

## 推荐托管：GitHub Pages

这个仓库已经带有 `.github/workflows/pages.yml`：你每次把新的 `.deb` 推送到 `main`，GitHub Actions 会自动运行 `build.py`，重新生成 `Packages`、`Packages.gz`、`Release`，然后部署到 Pages。

首次部署：

1. 在 GitHub 新建一个仓库，例如 `sinpoce-repo`。
2. 上传本目录里的全部内容，注意要上传 `index.html`、`build.py`、`debs/` 和 `.github/`，不要再套一层 `ios-personal-repo` 文件夹。
3. 打开仓库的 **Settings → Pages**，将 **Source** 设为 **GitHub Actions**。
4. 等待 **Actions** 中的 `Build and deploy repo` 完成。

源地址一般是：

```text
https://你的用户名.github.io/sinpoce-repo/
```

GitHub Pages 适合小型个人源；通过网页上传单个文件限制为 25 MiB，命令行推送单个文件可到 100 MiB，GitHub Pages 也不能直接使用 Git LFS。较大的软件包建议改用 Cloudflare Pages 或对象存储。

## 使用方法

1. 把自己的 `.deb` 文件放入 `debs/`。
2. 修改 `repo.json` 里的源名称和描述。
3. 如果使用上面的 GitHub Actions，只需提交并推送：

   ```bash
   git add debs/你的插件.deb repo.json
   git commit -m "Add package"
   git push
   ```

   Actions 会自动构建索引并发布。

   如果不使用 Actions，则在此目录运行：

   ```powershell
   .\build.ps1
   ```

   或：

   ```bash
   python3 build.py
   ```

如果要重新生成仓库自带的测试包，先运行：

```powershell
py -3 .\make-test-deb.py
```

4. 将整个目录部署到静态网站，并在越狱设备中添加网站根地址，末尾保留 `/`。

例如：

```text
https://你的用户名.github.io/你的仓库/
```

## 注意事项

- 这是未签名的个人源，只安装你自己信任的 `.deb`。
- 软件包的 `Architecture`、rootless/rootful 类型必须和设备及越狱环境匹配。
- 新增或替换 `.deb` 后，必须重新运行构建脚本，让 `Packages`、`Packages.gz` 和 `Release` 同步更新。
- 如果 `.deb` 使用 `control.tar.zst`，请改用能解压 zstd 的环境，或先重新打包为 gzip/xz/bz2 控制归档。
- `icon.svg` 可作为网页图标；如果某个客户端要求 PNG，请自行转换后命名为 `icon.png`。
