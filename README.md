## awesome-python3-webapp

> 本项目是基于[廖雪峰的python教程](https://www.liaoxuefeng.com/wiki/0014316089557264a6b348958f449949df42a6d3a2e542c000)写的blog项目。

### 下面是建立本地git项目的部分操作语句

>  当批量增加空文件夹时，可以在GIT库的根目录下输入命令行

    find . \( -type d -empty \) -and \( -not -regex ./\.git.* \) -exec touch {}/.gitkeep \;

>该语句可以在所有的空文件夹下增加.gitkeep文件(当然也可以改成任何你喜欢的后缀)
***


 1. 在本地创建一个版本库（即文件夹），通过`git init`把它变成Git仓库；
 2. 把项目复制到这个文件夹里面，再通过`git add .`把项目添加到仓库；
 3. 再通过`git commit -m "注释内容"`把项目提交到仓库；
 4. 在Github上设置好SSH密钥后，新建一个远程仓库，通过`git remote add origin `
    
        https://github.com/***.git将本地仓库和远程仓库进行关联；
 5. 最后通过`git push -u origin master`把本地仓库的项目推送到远程仓库（也就是Github）上；（若

新建远程仓库的时候自动创建了README文件会报错，解决办法看上面）

6. `git push origin master`  提交到github
