* 打包 window
  * cd /d D:\XXXXX\YearEndParty21_server
  * virtualenv yep21ServerPackage
  * .\yep21ServerPackage\Scripts\activate
  * pip install -r .\requirements.txt
  * pyinstaller --clean --onefile --hidden-import=main .\main.py
  * .\yep21ServerPackage\Scripts\deactivate

* 依赖
  * pip install -r .\requirements.txt


* 服务端更新：
** v1.2.2
1.优化网页界面布局
2.优化无用提示，现在返回的Alert只有在非 1000与2000才会有提示。使抽奖时的操作更流畅了一点
3.修复了数字池时，工号为 001 这种数据被转化为 1 的问题

* 前端更新：
** v1.1.3
1.修复了数字池工号显示为数字的问题
2.优化了数字池时，图片的包边发光会被设置为 不发光
3.修复了分辨率设置高为 4096时会被取整至 4100的问题

** v1.1.4
1.更新结果界面图片,使中间透明度更高可以看清楚星空
2.添加结果界面右下角解释提示文字
3.微调星空背景效果

** v1.1.5
1.更新特殊显示效果

** v1.1.6
1.修复当阶段在初始化完成前直接切换的问题