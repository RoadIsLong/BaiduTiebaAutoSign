# 百度贴吧自动签到Github Action版

## 今日签到状态 

![Baidu Tieba Auto Sign](https://github.com/RoadIsLong/TiebaSign/workflows/Baidu%20Tieba%20Auto%20Sign/badge.svg)

## 使用说明

1. Fork 本仓库，然后点击你的仓库右上角的 Settings，找到 Secrets 这一项，添加一个库秘密变量。其中 `BDUSS` 存放你的 BDUSS。支持同时添加多个帐户，BDUSS 之间用 `#` 隔开即可。

![添加库秘密变量](https://user-images.githubusercontent.com/30728105/165701800-ff57b82c-553d-4ddb-9687-d7be1c99801d.png)
![添加BDUSS](https://user-images.githubusercontent.com/30728105/165701943-d9086ff4-b251-437f-bb64-769f62fa730d.png)

2. 设置好环境变量后点击你的仓库上方的 `Actions` 选项，第一次打开需要点击 `I understand...` 按钮，确认在 Fork 的仓库上启用 GitHub Actions 。

3. 任意发起一次commit，可以参考下图流程修改readme文件。

- 打开`README.md`，点击修改按钮

![修改README](https://user-images.githubusercontent.com/30728105/165702570-e07bdd1d-752e-4d30-9994-af850f84ee32.png)

- 修改任意内容，这里在末尾插入了空格。移动到最下面，点击提交。

![添加空行](https://user-images.githubusercontent.com/30728105/165702845-0c918257-ea11-4a9d-90c1-814054d6a20e.png)

4. 至此自动签到就搭建完毕了，可以再次点击`Actions`查看工作记录，如果有`Baidu Tieba Auto Sign`则说明workflow创建成功了。点击右侧记录可以查看详细签到情况

![查看Action](https://user-images.githubusercontent.com/30728105/165702128-f364cda8-ceec-4b14-a5af-67c34b9de005.png)
