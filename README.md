## use guild
```
python -m grpc_tools.protoc -I ./ --python_out=./ --grpc_python_out=. ./protobufs/werewolf_kill.proto
```


## 固定角色位置
* step1: 打開 environment.py
* step2: 到 line 15.，你會看到以下程式碼，1) 註解line 15. 2) 打開 line 18.的註解 即可固定角色位置
```
    def __init__(self,role_list:list , random_assigned:bool=False):

        # game's initial setting
        random_assigned = False
        # role setting
        self.role_list = [ idx for idx ,value in enumerate(role_list) for _ in range(value)]
        #!! 打開註解，設定成你要固定角色，目前預設的是產生gameinfo的順序
        # 0: 預言家, 1: 女巫, 2: 平民, 3:狼人, 4: 獵人
        # self.role_list = [3, 2, 0, 3, 1, 2, 4]
```

## 固定發言順序
* step1: 打開 environment.py
* step2: 到 line 554.，你會看到以下程式碼，1) 註解line 554. 2) 打開 line 556.的註解 即可固定發言順序
```
    if self.first_comment_id_idx == None:
        self.first_comment_id_idx = random.randint(a=0,b=(len(self.id)-1))
        #!! 打開註解，設定成你要的發言順序，目前預設的是從第一個號碼最小的活著玩家
        # self.first_comment_id_idx = self.__get_live_id_list__()[0]
        self.current_comment_id_idx = self.first_comment_id_idx
```