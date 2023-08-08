import collections 
import random 
import json
from role import role


class env():

    # id : user_id , 
    def __init__(self,role_list:list , random_assigned:bool=False):

        # game's initial setting
        
        # role setting
        self.role_list = [ idx for idx ,value in enumerate(role_list) for _ in range(value)]
        self.num_player = len(self.role_list)
        self.random_assigned = random_assigned
        self.list_players = [0 for _ in range(self.num_player)]

        self.dict_player_number_to_roles = dict()
        self.dict_role_to_id = dict()
        self.num_village = 0 
        self.num_werewolf = 0
        self.num_god = 0

        with open("./role_setting.json") as file:
            self.dict_role_setting = json.load(file)

        # env setting
        self.round = 0
        self.state = 0
        self.game_record = dict()
        self.current_stage_name = ""
        self.dict_operations = {
            "werewolf_dialogue" : self.__save_dialogue__,
            "werewolf" : self.__player_vote__,
            "seer" : self.__seer_check_id_identity__,
            "witch" : [self.__witch_kill__,self.__witch_save__],
            "dialogue" : self.__save_dialogue__,
            "vote1" : self.__player_vote__,
            "vote2" : self.__player_vote__,
            "hunter" : [self.__hunter_kill__,self.__save_dialogue__],
            "check" : self.__save_dialogue__
        }
        # game's executing environment
        self.list_died_id = list()
        self.list_dialogue_id = list()
        self.list_chat_id = list()

        # operating id 
        self.id = list()
        # be operated id
        self.target_id = list()
        # be voted ids
        self.candidate_id = list()

        self.check_werewolf_res = True
        # second time vote 
        self.need_vote2 = False
        # need to go werewolf dialogue stage
        self.need_werewolf_dialogue = True
        # first comment id 
        self.first_comment_id_idx = None
        self.current_comment_id_idx = None
        # check end game 
        self.check_end = False


        self.next_stage = self.__night__
        self.next_stage_use = dict()

    def start_game(self)->list:
        
        self.__assign_role__()
        
        self.dict_player_number_to_roles = {idx:self.dict_role_setting[str(each)]["role"] for idx,each in enumerate(self.role_list)}
        for key, value in self.dict_player_number_to_roles.items():
            if value not in self.dict_role_to_id.keys():
                self.dict_role_to_id[value] = list()
            self.dict_role_to_id[value].append(key)
        
        return self.role_list

    def __assign_role__(self):

        if self.random_assigned:
            self.role_list = random.sample(self.role_list , self.num_player)

        for idx in range(self.num_player):
            self.list_players[idx] = role( self.dict_role_setting[str(self.role_list[idx])])
            if self.list_players[idx].role == "village":
                self.num_village += 1
            elif self.list_players[idx].role == "werewolf":
                self.num_werewolf += 1
            else :
                self.num_god += 1
    
    def check_role_list(role_list:list)->bool:
        role_list = [ idx for idx ,value in enumerate(role_list) for _ in range(value)]
        return role_list.count(0) == 1 and role_list.count(1) == 1 and role_list.count(4) <= 1 and  (len(role_list)-role_list.count(3)) >  (role_list.count(3)+1)
    
    def get_game_env(self):

        return f"""
Stage: {self.__get_current_stage__()}
Game Setting: {[f"player {key}: {value}" for key, value in self.dict_player_number_to_roles.items()]}
god number: {self.num_god}, village number: {self.num_village}, werewolf number: {self.num_werewolf}
all player's state: {[f"player {idx}: {state}" for idx , state in enumerate(self.__get_all_player_state__()
        )]}
        """

    def player_operation(self,id:int,operation:str, target_id:int, description:str,current_stage:str)->bool:
        print(current_stage , self.__get_current_stage__())
        if current_stage != self.__get_current_stage__():
            return False

        c_stage = current_stage.split("-")[2]

        # 沒寫存狼人發言
        if c_stage in ["werewolf_dialogue","dialogue"]:
            if self.need_vote2:
                c_stage = "vote_dialogue"
            return self.dict_operations[c_stage](id=id,content=description,mode=c_stage)
        elif c_stage in ["witch"]:
            use_idx = 0 if description == "poison" else 1
            return self.dict_operations[c_stage][use_idx](id = id,target_id=target_id)
        elif c_stage in ["hunter"]:
            if operation == "vote_or_not":
                return self.dict_operations[c_stage][0](id=id,target_id=target_id)
            else:
                return self.dict_operations[c_stage][1](id=id,content=description,mode="died")
        elif c_stage in ["check"]:
            return self.dict_operations[c_stage](id=id,content=description,mode="died")
        else:
            return self.dict_operations[c_stage](id=id,target_id=target_id)
        
    def stage(self):
        print(f"\ngam record : {self.game_record}")
        print(f"dialogue: {self.list_dialogue_id}")
        print(f"died: {self.list_died_id}")
        print(f"chat: {self.list_chat_id}")
        ret = list()
        self.current_stage_name = "check"
        ret = self.__priority_info__(ret)
        
        if len(ret) != sum([ 1 for idx in ret if idx[1] == "chat"]):
            return ret , self.__get_current_stage__()
        ret = self.next_stage(ret=ret)

        return ret , self.__get_current_stage__()
    
    def __get_current_stage__(self)->str:
        return f"{str(self.round)}-{str(self.state)}-{self.current_stage_name}"
    
    def __night__(self,ret:list)->list:
        self.state = 0
        self.round += 1
        self.game_record[self.round] = dict()
        self.need_werewolf_dialogue = True
        self.need_vote2 = False
        self.first_comment_id_idx = None
        self.current_comment_id_idx = None
        
        ret.append([[],"other",[],"天黑請閉眼"])
        self.current_stage_name = "check"
        self.next_stage = self.__stage_dialogue__
        return ret
    
    def __day__(self):
        self.state = 1
        self.need_werewolf_dialogue = False
        self.first_comment_id_idx = None
        self.current_comment_id_idx = None

    def __priority_info__(self,ret:list)->list:
        
        for get_dialogue , id in self.list_chat_id:
            target = []
            if self.need_werewolf_dialogue :
                target = self.id
            # 前面說話資訊
            ret.append([[id],"chat",target,get_dialogue(id=id)])
        # reset list
        self.list_chat_id.clear()
        # 接下來要進入 狼發言 , 
        if self.next_stage == self.__night__  and self.first_comment_id_idx != None and self.first_comment_id_idx == self.current_comment_id_idx and self.state == 1:
            if not self.__get_vote_res__():
                # vote1 
                if not self.need_vote2: 
                    self.need_vote2 = True
                    self.first_comment_id_idx = None
                    self.current_comment_id_idx = None
                    self.next_stage = self.__stage_dialogue__
                    ret.append([[],"other",[],"第一輪平票/沒人投票"])
            else :
                self.check_end = True
        
        for kind , id in  self.list_died_id:
            # 誰死了
            ret.append(kind(id=id))
        self.list_died_id.clear()

        if len(self.list_dialogue_id) != 0:
            # 死的人發遺言
            
            if self.list_dialogue_id[0][1] == 0:
                ret.insert(0,[[],"other",self.list_dialogue_id[0][0][0],"天亮請睜眼，$請發表遺言"])
            elif self.list_dialogue_id[0][1] == 1:
                ret.insert(0,[[],"other",self.list_dialogue_id[0][0][0],"$被票出去了，請發表遺言"])
            else:
                ret.insert(0,[[],"other",self.list_dialogue_id[0][0][0],"$被獵人殺死了，請發表遺言"])
            ret.append(self.list_dialogue_id[0][0])
            self.id = self.list_dialogue_id[0][0][0]
            # 有發言下個stage就有chat
            self.list_chat_id.append([self.__get_current_died_dialogue__,self.list_dialogue_id[0][0][0][0]])
            self.list_dialogue_id.pop(0)
            # for need to use skill player when they died
            try :
                # 死的人有技能
                if self.list_dialogue_id[0][1] in ["vote_or_not","vote"]:
                    ret.append(self.list_dialogue_id[0])
                    self.list_dialogue_id.pop(0)

            except:
                pass

        if self.check_end :
            end_game_res = self.__check_end_game__() 
            if end_game_res != None:
                ret.append(end_game_res)
            if self.state == 0:
                self.__day__()
                if self.round != 1 and (self.__get_current_killed_id__() != None or self.__get_current_poisoned_id__() != None):
                    ret.insert(0,[[],"other",[],"天亮請睜眼"])
            self.check_end = False

        return ret

    def __get_end_game_res__(self)->str:
        
        if self.num_werewolf == (self.num_god + self.num_village) :
            return "遊戲結束 狼人過半 壞人獲勝"
        elif self.num_god <= 0 :
            return  "遊戲結束 神職全死 壞人獲勝"
        elif self.num_village <= 0 :
            return "遊戲結束 村民全死 壞人獲勝"
        elif self.num_werewolf <= 0:
            return "好人陣營獲勝"
        elif self.__get_current_killed_id__() == None and self.__get_current_poisoned_id__() == None and self.state == 0:
            return "天亮請睜眼，昨晚是平安夜"
        elif self.__get_current_voted_id__() == None and self.state == 1:
            return "沒有人被投出去"
        
        return None
    
    def __check_end_game__(self)->list:
        description = self.__get_end_game_res__()
        if description in ["天亮請睜眼，昨晚是平安夜","沒有人被投出去"]:
            return [[], "other", [], description]
        elif description != None:
            return [[], "end", [], description]
        return None
    
    def __killed_by_werewolf__(self,id:int)->list:
        if self.round == 1:
            self.list_dialogue_id.append([[[id],"dialogue",[],"發遺言"],0])
        
        if self.role_list[id] == 4:
            self.id = [id]
            self.target_id = self.__get_target_list__(vote=True)
            self.list_dialogue_id.append([self.id,"vote_or_not",self.target_id,"獵人殺人"])
            self.current_stage_name = "hunter"

        return [[id],"died",[],"昨晚死了"]
    
    def __killed_by_witch__(self,id:int)->list:
        if self.round == 1:
            self.list_dialogue_id.append([[[id],"dialogue",[],"發遺言"],0])
        
        return [[id],"died",[],"昨晚死了"]
    
    def __killed_by_hunter__(self,id:int)->list:

        self.list_dialogue_id.append([[[id],"dialogue",[],"發遺言"],2])
        return [[id],"died",[],"被獵人殺了"]

    def __killed_by_vote__(self,id:int)->list:

        self.list_dialogue_id.append([[[id],"dialogue",[],"發遺言"],1])
        if self.role_list[id] == 4:
            self.id = [id]
            self.target_id = self.__get_target_list__(vote=True)
            self.list_dialogue_id.append([self.id,"vote_or_not",self.target_id,"獵人殺人"])
            self.current_stage_name = "hunter"
        
        return [[id],"died",[],"被票出去了"]

    def __get_role_id_list__(self,role:str,night_mode:bool=False)->list:
        
        try:
            live_list = self.__get_live_id_list__()
            if night_mode :
                for id in [self.__get_current_killed_id__(),self.__get_current_poisoned_id__()]:
                    if id != None :
                        live_list.append(id)
            role_id_list = list()
            for id in self.dict_role_to_id[role]:
                if id in live_list:
                    role_id_list.append(id)
            return role_id_list
        except:
            return None

    def __get_target_list__(self,night_mode:bool=False,vote:bool=False)->list:
        
        target_list = self.__get_live_id_list__()
        if night_mode :
            for id in [self.__get_current_killed_id__(),self.__get_current_poisoned_id__()]:
                if id != None :
                    target_list.append(id)
        if not vote:
            target_list.append(-1)
        target_list.sort()
        return target_list

    def __get_live_id_list__(self):
        return [id for id , player_state in enumerate(self.__get_all_player_state__()) if player_state == 1]
    
    def __get_all_player_state__(self):
        return [id.state for id in self.list_players]
    # v
    def __stage_werewolf__(self,ret:list)->list:
        
        self.id = self.__get_role_id_list__(role="werewolf",night_mode=True)
        self.target_id = self.__get_target_list__(night_mode=True,vote=True)
        self.need_werewolf_dialogue = False
        self.__reset_vote__()
        ret.append([self.id,"vote",self.target_id,"狼人投票殺人"])
        self.next_stage = self.__stage_seer__
        self.current_stage_name = "werewolf"
        return ret
    
    def __stage_seer_reply__(self,stage:list):
        
        
        # 可能沒有驗，要隨機
        see_id = stage[2][0]()
        if see_id == None:
            see_id = random.choice(self.target_id)
            self.__seer_check_id_identity__(id=stage[0][0],target_id=see_id)
        stage[2][0] = see_id
        stage[3]= f"{self.list_players[see_id].identity}"
        

        return stage
    # v
    def __stage_seer__(self,ret:list)->list:

        self.id = self.__get_role_id_list__(role="seer",night_mode=True)
        self.target_id = self.__get_target_list__(night_mode=True,vote=True)
        if len(self.id) != 0:
            self.target_id.remove(self.id[0])
            ret.append([self.id,"vote",self.target_id,"預言家查身分"])
            self.next_stage_use[self.__stage_witch__] = [self.id,"role_info",[self.__get_current_seer_id__],""]
        else :
            ret.append([self.id,"vote",[],"預言家查身分"])

        self.next_stage = self.__stage_witch__
        self.current_stage_name = "seer"
        return ret
    
    def __kill_or_save__(self,target_id:int,mode:int):
        
        state = 1 if mode == 1 else 0

        if self.list_players[target_id].state == state :
            return 
        # change state
        self.list_players[target_id].__update_state__(state= state)

        # update number of village, werewolf, god
        if self.list_players[target_id].role == "village":
            self.num_village += mode
        elif self.list_players[target_id].role == "werewolf":
            self.num_werewolf += mode 
        else :
            self.num_god += mode

    def __get_werewolfKill_res__(self):
        
        list_current_vote = self.check_player_voted_state()
        list_live_id = self.__get_role_id_list__(role="werewolf",night_mode=True)
        list_target_id = self.__get_target_list__(vote=True)

        dict_vote_res = dict() 
        for id in list_live_id:
            if list_current_vote[id] == -1:
                continue
            if list_current_vote[id] not in dict_vote_res.keys():
                dict_vote_res[list_current_vote[id]] = list()
            dict_vote_res[list_current_vote[id]].append(id)
        
        # 投票人數 
        num_vote = sum([len(val) for val in dict_vote_res.values()])
        killed_id = None
        if num_vote == 0:
            killed_id = random.choice(list_target_id)
        else:
            # get maximum voted id
            candidate_id = [key for key , val  in dict_vote_res.items() if val == max(dict_vote_res.values())]
            killed_id = candidate_id[0]
            if len(self.candidate_id) != 1:
                killed_id = random.choice(candidate_id)
        self.__kill_or_save__(target_id=killed_id,mode=-1)
        self.list_died_id.append([self.__killed_by_werewolf__,killed_id])
        self.__save_game_record__(id=killed_id,kind="werewolf")

    def __seer_check_id_identity__(self,id:int,target_id:int)->bool:
        copy_target_id = self.target_id.copy()
        copy_target_id.insert(0,-1)
        if id not in self.id or target_id not in copy_target_id:
            return False
        if id == -1:
            return True
        self.__save_game_record__(id=target_id,kind="seer")
        return True
    
    def __witch_kill__(self,id:int,target_id:int)->bool:
        copy_target_id = self.target_id.copy()
        copy_target_id.insert(0,-1)
        if id not in self.id or target_id not in copy_target_id or self.__get_current_saved_id__() != None:
            return False
        
        poisoned_id  =self.__get_current_poisoned_id__()
        # 已經有了的話
        if  poisoned_id != None:
            self.__kill_or_save__(target_id=poisoned_id,mode=1)
            self.list_died_id.remove([self.__killed_by_witch__,poisoned_id])
            self.__clear_current_game_record__(kind="poisoned")
            self.list_players[id].kill_times += 1
        if target_id == -1 :
            return True
        self.__kill_or_save__(target_id=target_id,mode=-1)
        self.list_died_id.append([self.__killed_by_witch__,target_id])
        self.__save_game_record__(id=target_id,kind="poisoned")
        self.list_players[id].kill_times -= 1
        return True
    
    def __witch_save__(self,id:int,target_id:int)->bool:
    
        if id not in self.id or target_id not in [-1,self.__get_current_killed_id__()] or self.__get_current_poisoned_id__() != None:
            return False
        
        saved_id  =self.__get_current_saved_id__()
        # 已經有了的話
        if  saved_id != None:
            self.__kill_or_save__(target_id=saved_id,mode=-1)
            self.__clear_current_game_record__(kind="saved")
            self.list_died_id.append([self.__killed_by_werewolf__,saved_id])
            self.__save_game_record__(id=saved_id,kind="werewolf")
            self.list_players[id].save_times += 1
        if target_id == -1 :
            return True
        
        self.__clear_current_game_record__(kind="werewolf")
        self.list_died_id.remove([self.__killed_by_werewolf__,target_id])
        self.__kill_or_save__(target_id=target_id,mode=1)
        self.__save_game_record__(id=target_id,kind="saved")
        self.list_players[id].save_times -= 1
        return True
    
    def __witch_has_save__(self)->bool:
                
        if self.list_players[self.id[0]].save_times > 0 :
            return True
        return False

    def __witch_has_kill__(self)->bool:
        if self.list_players[self.id[0]].kill_times > 0 :
            return True
        return False
    
    def __hunter_kill__(self,id:int,target_id:int)->bool:
        copy_target_id = self.target_id.copy()
        copy_target_id.insert(0,-1)
        if id not in self.id or target_id not in copy_target_id:
            return False
        
        hunterKill_id  =self.__get_current_hunterKilled_id__()
        # 已經有了的話
        if  hunterKill_id != None:
            self.__kill_or_save__(target_id=hunterKill_id,mode=1)
            self.list_died_id.remove([self.__killed_by_hunter__,hunterKill_id])
            self.__clear_current_game_record__(kind="hunterKilled")
            self.list_players[id].kill_times += 1
        if target_id == -1 :
            return True

        self.__kill_or_save__(target_id=target_id,mode=-1)
        self.list_died_id.append([self.__killed_by_hunter__,target_id])
        self.__save_game_record__(id=target_id,kind="hunterKilled")
        self.list_players[id].kill_times -= 1
        return True
    # v 
    def __stage_witch__(self,ret:list)->list:
        
        self.__get_werewolfKill_res__()
        if self.next_stage_use[self.__stage_witch__] != None:
            ret.append(self.__stage_seer_reply__(stage=self.next_stage_use[self.__stage_witch__]))
            self.next_stage_use[self.__stage_witch__] = None

        self.id = self.__get_role_id_list__(role="witch",night_mode=True)
        self.target_id = self.__get_target_list__(night_mode=True,vote=True)
        if len(self.id) != 0:

            if self.__witch_has_save__():
                ret.append([self.id,"vote_or_not",[self.__get_current_killed_id__()],"女巫救人"])
            if self.__witch_has_kill__():
                self.target_id.pop(self.id[0])
                ret.append([self.id,"vote_or_not",self.target_id,"女巫毒人"])
            
        else :
            ret.append([self.id,"vote_or_not",[],"女巫救人"])
            ret.append([self.id,"vote_or_not",[],"女巫毒人"])
        
        self.next_stage = self.__stage_dialogue__
        self.current_stage_name = "witch"
        self.check_werewolf_res = False
        self.check_end = True
        return ret

    def __stage_dialogue__(self,ret:list)->list:
        self.id = self.__get_live_id_list__()
        self.current_stage_name = "dialogue"
        operation_name = "dialogue"
        get_dialogue_func = self.__get_current_live_dialogue__
        next_stage = self.__stage_vote__
        
        if self.need_werewolf_dialogue:
            self.id = [idx for idx , role in enumerate(self.role_list) if role == 3]
            self.current_stage_name = "werewolf_dialogue"
            get_dialogue_func = self.__get_current_werewolf_dialogue__
            next_stage = self.__stage_werewolf__
            operation_name = "werewolf_dialogue"

        if self.need_vote2:
            self.__setting_vote2_id_and_target_id__()
            # target id才要發言
            self.id =self.target_id
        
        if self.first_comment_id_idx == None:
            self.first_comment_id_idx = random.randint(a=0,b=(len(self.id)-1))
            self.current_comment_id_idx = self.first_comment_id_idx

        # 目前玩家要發言
        ret.append([[self.id[self.current_comment_id_idx]],operation_name,[],"玩家發言"])
        # 下個stage 顯示的發言
        if self.list_players[self.id[self.current_comment_id_idx]].state == 1:
            self.list_chat_id.append([get_dialogue_func,self.id[self.current_comment_id_idx]])
        self.next_stage = self.__stage_dialogue__

        if self.current_comment_id_idx == ((self.first_comment_id_idx-1)+len(self.id)) % len(self.id):  
            self.next_stage = next_stage

        self.current_comment_id_idx = (self.current_comment_id_idx + 1) % len(self.id)
        return ret
    # v
    def __stage_vote__(self,ret:list)->list:
        
        self.id = self.__get_live_id_list__()
        self.target_id = self.__get_target_list__(vote=True)
        self.current_stage_name = "vote1"
        if self.need_vote2:
            self.__setting_vote2_id_and_target_id__()
            self.current_stage_name = "vote2"
            self.check_end = True
        self.__reset_vote__()
        ret.append([self.id,"vote_or_not",self.target_id,"投票階段"])
        self.next_stage = self.__night__
        return ret
    
    def __get_vote_res__(self)->bool:
        
        if self.__get_current_voted_id__() != None:
            return True
        list_current_vote = self.check_player_voted_state()
        list_live_id = self.__get_live_id_list__()
        
        dict_vote_res = dict() 
        for id in list_live_id:
            if list_current_vote[id] == -1:
                continue
            if list_current_vote[id] not in dict_vote_res.keys():
                dict_vote_res[list_current_vote[id]] = list()
            dict_vote_res[list_current_vote[id]].append(id)
        
        # 投票人數 
        num_vote = sum([len(val) for val in dict_vote_res.values()])
        print(num_vote)
        # 都沒投
        if num_vote == 0:
            self.candidate_id = list_live_id
            return False
        # 全部有投
        # 部分有投
        else:
            # get maximum voted id
            self.candidate_id = [key for key , val  in dict_vote_res.items() if len(val) == max([len(val) for val in dict_vote_res.values()])]
            if self.need_vote2 and len(self.candidate_id) != 1:
                self.candidate_id = random.sample(self.candidate_id,1)

            if len(self.candidate_id) == 1:
                self.__kill_or_save__(target_id=self.candidate_id[0],mode=-1)
                self.list_died_id.append([self.__killed_by_vote__,self.candidate_id[0]])
                self.__save_game_record__(id=self.candidate_id[0],kind="voted")
                return True
            return False            
    
    def __reset_vote__(self):
        for each_id in self.list_players:
            each_id.current_vote_player_number = -1

    def check_player_voted_state(self)->list:

        list_current_vote = [-1 for _ in range(self.num_player)]
        for idx , id in enumerate(self.list_players):
            list_current_vote[idx] = id.current_vote_player_number 
        
        return list_current_vote

    def __setting_vote2_id_and_target_id__(self):

        self.id = self.__get_live_id_list__()
        self.target_id = self.candidate_id
        if self.id != self.target_id :
            for id in self.target_id:
                if id in self.id:
                    self.id.remove(id)
    
    def __player_vote__(self,id,target_id):
        copy_target_id = self.target_id.copy()
        copy_target_id.insert(0,-1)
        if id not in self.id or target_id not in copy_target_id:
            return False
        
        self.list_players[id].__vote__(target_id)
        return True

    def __clear_current_game_record__(self,kind:str):
        try:
            self.game_record[self.round].pop(kind)
        except:
            print("ERROR: can not find key of record!")

    def __save_game_record__(self,id:int,kind:str):
        
        try:
            self.game_record[self.round][kind] = id
        except:
            print("ERROR: can not find key of record!")

    def __get_game_record_by_round__(self,round:int,kind:str):
        
        try:
            return self.game_record[round][kind]
        except:
            return None

    def __get_current_killed_id__(self):
        return self.__get_game_record_by_round__(round=self.round,kind="werewolf")
    
    def __get_current_seer_id__(self):
        return self.__get_game_record_by_round__(round=self.round,kind="seer")
        
    def __get_current_poisoned_id__(self):
        return self.__get_game_record_by_round__(round=self.round,kind="poisoned")

    def __get_current_saved_id__(self):
        return self.__get_game_record_by_round__(round=self.round,kind="saved")

    def __get_current_hunterKilled_id__(self):
        return self.__get_game_record_by_round__(round=self.round,kind="hunterKilled")

    def __get_current_voted_id__(self):
        return self.__get_game_record_by_round__(round=self.round,kind="voted")

    def __save_dialogue__(self,id:int,content:str,mode:str)->bool:
        
        if id not in self.id  :
            return False
        if mode == "dialogue":
            print(self.id,self.current_comment_id_idx)
            if id != self.id[self.current_comment_id_idx]:
                return False
            if self.round not in self.list_players[id].dialogues.keys():
                
                self.list_players[id].dialogues[str(self.round)] = list()
            self.list_players[id].dialogues[str(self.round)].append(content)
        elif mode == "died":
            if self.round not in self.list_players[id].dialogues.keys():
                self.list_players[id].dialogues["died_dialogue"] = list()
            self.list_players[id].dialogues["died_dialogue"].append(content)
        elif mode =="werewolf_dialogue":
            if id != self.id[self.current_comment_id_idx]:
                return False
            if self.round not in self.list_players[id].dialogues.keys():
                self.list_players[id].dialogues["werewolf"+str(self.round)] = list()
            self.list_players[id].dialogues["werewolf"+str(self.round)].append(content)
        ### werewolf_dialogue
        return True

    def __get_dialogue_by_round__(self,id:int,kind:str)->str:
        dialogues = ""
        try:
            for dialogue in self.list_players[id].dialogues[kind]:
                dialogues+=dialogue
            return dialogues
        except:
            return dialogues

    def __get_current_live_dialogue__(self,id:int)->str:
        return self.__get_dialogue_by_round__(id=id,kind=str(self.round))

    def __get_current_died_dialogue__(self,id:int)->str:
        return self.__get_dialogue_by_round__(id=id,kind="died_dialogue")
        
    def __get_current_werewolf_dialogue__(self,id:int):
        return self.__get_dialogue_by_round__(id=id,kind="werewolf"+str(self.round))
    
    





if __name__ == "__main__":
    
    env = env(role_list=[1,1,2,2,1],random_assigned=False)

    print(env.start_game())
    # env.__night__()
    op  , stage = env.stage()
    print(op,stage)

    op  , stage = env.stage()
    print(op,stage)

    print(env.player_operation(id=op[0][0][0],operation="dialogue",target_id=-1,description="hello",current_stage=stage))

    op  , stage = env.stage()
    print(op,stage)
    print(env.player_operation(id=op[1][0][0],operation="dialogue",target_id=-1,description="hihi",current_stage=stage))
    
    # 狼殺人
    op  , stage = env.stage()
    print(op,stage)
    print(env.player_operation(id=4,operation="vote",target_id=2,description="",current_stage=stage))
    print(env.player_operation(id=4,operation="vote",target_id=7,description="",current_stage=stage))
    print(env.player_operation(id=5,operation="vote",target_id=6,description="",current_stage=stage))
    print(env.player_operation(id=5,operation="vote",target_id=-1,description="",current_stage=stage))
    print(env.player_operation(id=5,operation="vote",target_id=6,description="",current_stage=stage))
    print(env.check_player_voted_state())

    # 預言家
    op  , stage = env.stage()
    print(op,stage)
    print(env.player_operation(id=0,operation="vote",target_id=4,description="",current_stage=stage))
    print(env.player_operation(id=0,operation="vote",target_id=2,description="",current_stage=stage))

    # 女巫
    op  , stage = env.stage()
    print(op,stage)
    #print(env.player_operation(id=1,operation="vote_or_not",target_id=4,description="save",current_stage=stage))
    # print(env.player_operation(id=1,operation="vote",target_id=-1,description="",current_stage=stage))
    print(env.player_operation(id=1,operation="vote_or_not",target_id=2,description="poison",current_stage=stage))

    # check
    op  , stage = env.stage()
    print(op,stage)
    print(env.player_operation(id=6,operation="vote_or_not",target_id=4,description="",current_stage=stage))
    # print(env.player_operation(id=4,operation="dialogue",target_id=-1,description="abc",current_stage=stage))

    op  , stage = env.stage()
    print(op,stage)

    op  , stage = env.stage()
    print(op,stage)
    print("/////")
    # print(env.player_operation(id=2,operation="dialogue",target_id=-1,description="qqqqqq",current_stage=stage))

    # op  , stage = env.stage()
    # print(op,stage)
    # print(env.player_operation(id=4,operation="dialogue",target_id=-1,description="1234",current_stage=stage))
    # 0 , 1 , 3 , 5 
    # env.__day__()
    print("!!!!!")
    for _ in range(4):
        op  , stage = env.stage()
        print(op,stage)
        print(env.player_operation(id=op[-1][0][0],operation="dialogue",target_id=-1,description="test",current_stage=stage))


    # 投票
    op  , stage = env.stage()
    print(op,stage)
    #print(env.player_operation(id=5,operation="vote_or_not",target_id=6,description="",current_stage=stage))

    op  , stage = env.stage()
    print(op,stage)
    print("/////")
    #print(env.player_operation(id=6,operation="vote_or_not",target_id=4,description="",current_stage=stage))
   # print(env.player_operation(id=6,operation="dialogue",target_id=-1,description="abc",current_stage=stage))
    op  , stage = env.stage()
    print(op,stage)
    #print(env.player_operation(id=4,operation="dialogue",target_id=-1,description="1111",current_stage=stage))
    op  , stage = env.stage()
    print(op,stage)

    op  , stage = env.stage()
    print(op,stage)

    op  , stage = env.stage()
    print(op,stage)

    op  , stage = env.stage()
    print(op,stage)
    # print(env.player_operation(id=5,operation="vote",target_id=0,description="",current_stage=stage))

    op  , stage = env.stage()
    print(op,stage)

    op  , stage = env.stage()
    print(op,stage)

    op  , stage = env.stage()
    print(op,stage)

    for _ in range(4):
        op  , stage = env.stage()
        print(op,stage)

    op  , stage = env.stage()
    print(op,stage)
    print(env.player_operation(id=1,operation="vote_or_not",target_id=5,description="",current_stage=stage))
    print(env.player_operation(id=3,operation="vote_or_not",target_id=5,description="",current_stage=stage))
    print(env.player_operation(id=5,operation="vote_or_not",target_id=3,description="",current_stage=stage))
    print(env.player_operation(id=2,operation="vote_or_not",target_id=3,description="",current_stage=stage))
    print("///////////")
    print(env.check_player_voted_state())
    op  , stage = env.stage()
    print(op,stage)

    op  , stage = env.stage()
    print(op,stage)

    op  , stage = env.stage()
    print(op,stage)

    op  , stage = env.stage()
    print(op,stage)

    print(env.player_operation(id=1,operation="vote_or_not",target_id=3,description="",current_stage=stage))
    #print(env.player_operation(id=2,operation="vote_or_not",target_id=3,description="",current_stage=stage))
    
    op  , stage = env.stage()
    print(op,stage)
    print(env.player_operation(id=3,operation="dialogue",target_id=-1,description="ffffffff",current_stage=stage))
    
    op  , stage = env.stage()
    print(op,stage)

    op  , stage = env.stage()
    print(op,stage)

    op  , stage = env.stage()
    print(op,stage)

    op  , stage = env.stage()
    print(op,stage)

    op  , stage = env.stage()
    print(op,stage)

    op  , stage = env.stage()
    print(op,stage)

    op  , stage = env.stage()
    print(op,stage)
    # # print(env.player_operation(id=6,operation="vote_or_not",target_id=4,description="",current_stage=stage))
    # for _ in range(4):
    #     op  , stage = env.stage()
    #     print(op,stage)
    #     print(env.player_operation(id=op[-1][0][0],operation="dialogue",target_id=-1,description="gggggggggggg",current_stage=stage))
    
    # op  , stage = env.stage()
    # print(op,stage)
    # print(env.player_operation(id=5,operation="vote_or_not",target_id=1,description="",current_stage=stage))

    # op  , stage = env.stage()
    # print(op,stage)
    # print(env.player_operation(id=op[-1][0][0],operation="dialogue",target_id=-1,description="eeeeeeeee",current_stage=stage))

    # op  , stage = env.stage()
    # print(op,stage)
    # print(env.player_operation(id=op[-1][0][0],operation="dialogue",target_id=-1,description="gggggggggggg",current_stage=stage))

    # op  , stage = env.stage()
    # print(op,stage)
    # print(env.player_operation(id=op[-1][0][0],operation="dialogue",target_id=-1,description="gggggggggggg",current_stage=stage))

    # # env.__night__()
    # for _ in range(2):
    #     op  , stage = env.stage()
    #     print(op,stage)

    # print("!!")

    # op  , stage = env.stage()
    # print(op,stage)

    # op  , stage = env.stage()
    # print(op,stage)

    # op  , stage = env.stage()
    # print(op,stage)

    # op  , stage = env.stage()
    # print(op,stage)