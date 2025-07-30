# Git团队协作指南

这个指南将帮助团队成员学习如何使用Git进行协作开发，即使你之前没有使用过Git。

## 目录

1. [准备工作](#准备工作)
2. [基本协作流程](#基本协作流程)
3. [常见操作详解](#常见操作详解)
4. [常见问题与解决](#常见问题与解决)
5. [Git图形化工具](#Git图形化工具)

## 准备工作

### 1. 安装Git

- **Windows**: 下载并安装 [Git for Windows](https://gitforwindows.org/)
- **macOS**: 
  - 通过Terminal安装Homebrew: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
  - 然后安装Git: `brew install git`
- **Linux**: `sudo apt-get install git` (Ubuntu/Debian) 或 `sudo yum install git` (CentOS)

### 2. 配置Git

打开终端(Terminal)或命令提示符(Command Prompt)，运行以下命令：

```bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱@example.com"
```

### 3. 注册GitHub账号

如果你还没有GitHub账号，请前往[GitHub官网](https://github.com/)注册一个账号。

## 基本协作流程

我们采用"Fork & Pull Request"的协作模式，步骤如下：

### 1. Fork主仓库

1. 访问主仓库的GitHub页面
2. 点击右上角的"Fork"按钮，创建一个属于你自己的仓库副本

![Fork示意图](https://docs.github.com/assets/cb-23088/images/help/repository/fork-button.png)

### 2. 克隆你的Fork到本地

在Fork完成后，你会被重定向到你自己GitHub账号下的仓库副本。这时有两种方式可以克隆到本地：

**方式一：从你的GitHub仓库页面克隆**

1. 在你的GitHub仓库页面(通常是`https://github.com/你的用户名/hello-HTML`)，点击绿色的「Code」按钮
2. 复制显示的URL
3. 打开终端，执行以下命令：

```bash
git clone https://github.com/你的用户名/hello-HTML.git
cd hello-HTML
```

**方式二：直接用命令行**

如果你已经知道你的GitHub用户名，可以直接在终端执行：

```bash
git clone https://github.com/你的用户名/hello-HTML.git
cd hello-HTML
```

### 3. 设置上游仓库

这一步很重要，它可以让你的本地仓库知道原始仓库的位置，方便你后续同步更新：

```bash
git remote add upstream https://github.com/Cae1anSou/hello-HTML.git
```

你可以通过以下命令验证是否设置成功：

```bash
git remote -v
```

你应该能看到origin(你的Fork)和upstream(原始仓库)两个远程仓库地址。

### 4. 创建新分支

每次开发新功能或修复bug时，都应该创建一个新的分支：

```bash
git checkout -b 你的功能名称
# 例如: git checkout -b preview-module
```

### 5. 开发你的功能

按照[模块集成指南](./模块集成指南.md)和[前端模板使用指南](./前端模板使用指南.md)，在你的分支上开发功能。

### 6. 提交你的更改

```bash
# 查看你的更改
git status

# 添加更改的文件
git add .

# 提交更改
git commit -m "添加了预览模块功能"
```

### 7. 推送到你的Fork

```bash
git push origin 你的功能名称
# 例如: git push origin preview-module
```

### 8. 创建Pull Request

1. 访问你Fork的GitHub仓库页面
2. 点击"Pull Request"按钮
3. 点击"New Pull Request"
4. 选择你的功能分支和主仓库的主分支
5. 填写Pull Request的标题和描述，详细说明你做了什么更改
6. 点击"Create Pull Request"
7. 微信上和我说一下

## 常见操作详解

### 更新你的Fork

主仓库更新后，你需要更新你的Fork：

```bash
# 切换到主分支
git checkout main

# 获取主仓库的最新更改
git fetch upstream

# 将主仓库的更改合并到你的本地主分支
git merge upstream/main

# 推送更新到你的GitHub仓库
git push origin main
```

### 处理合并冲突

如果遇到合并冲突，你需要手动解决：

1. 打开有冲突的文件，找到标记为`<<<<<<<`, `=======`, `>>>>>>>`的部分
2. 编辑文件，解决冲突
3. 保存文件
4. 添加已解决冲突的文件：`git add 文件名`
5. 继续合并过程：`git merge --continue`

### 放弃本地更改

如果你想放弃本地更改，可以使用：

```bash
# 放弃所有未提交的更改
git reset --hard HEAD

# 放弃对特定文件的更改
git checkout -- 文件名
```

## 常见问题与解决

### 1. "Permission denied"错误

这通常是因为你没有权限推送到主仓库。确保你是推送到自己的Fork：

```bash
git remote -v  # 查看远程仓库
git push origin 你的分支名  # 推送到你的Fork
```

### 2. "Pull request has conflicts"

这意味着你的分支与主分支有冲突，需要先解决冲突：

```bash
git checkout main
git pull upstream main
git checkout 你的分支名
git merge main
# 解决冲突
git add .
git commit -m "解决合并冲突"
git push origin 你的分支名
```

### 3. 忘记创建分支直接在main上开发

如果你忘记创建分支，直接在main上开发了，可以这样补救：

```bash
# 创建一个新分支，包含当前更改
git checkout -b 新分支名

# 将main重置到之前的状态
git checkout main
git reset --hard origin/main

# 继续在新分支上开发
git checkout 新分支名
```

## Git图形化工具

如果你不习惯命令行，可以使用这些图形化工具：

- [GitHub Desktop](https://desktop.github.com/) - 简单易用，适合初学者
- [SourceTree](https://www.sourcetreeapp.com/) - 功能更强大
- [GitKraken](https://www.gitkraken.com/) - 界面美观，功能全面
- [Visual Studio Code](https://code.visualstudio.com/) - 如果你用VSCode编码，它内置了很好的Git支持


---

如有任何问题，可以随时联系我！