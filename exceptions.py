class AwardDataError(Exception):
    pass

class PoolDataFileError(Exception):
    def __init__(self, value=""):
        self.value = value
    def __str__(self):
        return(repr("查找不到以下用户池文件：{}".format(self.value)))

class AwardMultiplyRow(Exception):
    pass

class AwardIDDuplicate(Exception):
    pass

class PoolIDMultiplyFile(Exception):
    pass

class AwardFormateError(Exception):
    def __str__(self):
        must_have_column_list = ["用户是否可抽中多奖品","用户池","用户池列表名字","奖品名字","奖品数目","奖品图片名字"]
        return(repr("【{}】".format(must_have_column_list)))

class AwardEmptyError(Exception):
    def __str__(self):
        must_have_column_list = ["用户是否可抽中多奖品","用户池","用户池列表名字","奖品名字","奖品数目","奖品图片名字"]
        return(repr("请检查以上各列,不能有空字符串：【{}】".format(must_have_column_list)))

class ImageNotExistError(Exception):
    def __init__(self, value=""):
        self.value = value
    def __str__(self):
        return(repr("查找不到以下图片文件：【{}】. \n请检查文件名字或 图片后缀,如.png .jpg等是否正确".format(self.value)))

class DrawStatgeError(Exception):
    def __init__(self, value=""):
        self.value = value
    def __str__(self):
        return(repr("抽奖阶段顺序有问题：【{}】".format(self.value)))