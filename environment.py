import collections 
import random 
import json
from role import role

class env():

    """
    0 : seer
    1 : witch 
    2 : village
    3 : werewolf
    4 : hunter
    """

    def __init__(self,roles :list, state = 0, round = 0):
        
        # env's state, night(0) and day(1)
        self.state = state
        # game current round
        self.round = round
        # number of god 
        self.num_god = 0
        # number of village 
        self.num_village = 0
        # number of werewolf
        self.num_werewolf = 0
        # role init setting
        with open("./role_setting.json") as file:
            self.dict_role_setting = json.load(file)
        
        # 遊戲角色配置
        self.roles_list = [ idx for idx ,value in enumerate(roles) for _ in range(value)]
        # number of player
        self.num_player = len(self.roles_list)

        self.current_stage = 0
        self.all_stage = ["werewolf","seer","witch","check_end1","check_end2","dialogue","vote1","vote2","hunter2","check_end3"]
        self.all_stage_func = [self.__stage_werewolf__,self.__stage_seer__,self.__stage_witch__,self.__stage_check_end1__,self.__stage_check_end2__,self.__stage_dialogue__,self.__stage_vote1__,self.__stage_vote2__,self.__stage_hunter2__,self.__stage_check_end3__]

        self.operation = {
            "werewolf" : self.__player_vote__,
            "seer" :  self.__seer_check_identity__,
            "witch": [self.__witch_poison__,self.__witch_save__],
            "check_end1" : self.__hunter_kill__,
            "dialogue" : self.__save_player_dialogue__,
            "vote1" : self.__player_vote__,
            "vote2" : self.__player_vote__,
            "hunter2" : self.__hunter_kill__,
        }


        self.list_has_commented_player_number = list()
        self.record = list()

        self.list_players = list()
        # init from which player comment 
        self.current_comment_player_number = 0
        self.end_comment_player_number = self.current_comment_player_number - 1
        self.number_comment = 0
  
    """  Server Use func """

    def start_game(self)->dict:
        """
        check minimum player and assign roles to all players.\n
        roles -> setting of game role \n
        return value :
            dict_assigned_roles -> {player x: 分配後的角色}
        """
        
        if not (int((len(self.roles_list)+1)/2) >  self.roles_list.count(3)) :

            print("at least one good identity")
            return 
        
        list_assigned_roles = self.__assign_roles__()

        self.dict_player_number_to_roles = {idx:self.dict_role_setting[str(each)]["role"] for idx,each in enumerate(list_assigned_roles)}


        return list_assigned_roles
    
    def stage(self)->tuple[list(),str]:
        # tuple[list,str,list,str]
        """
        return value : \n
        user id , operation ,  white list , description
        """
        
        list_live_player = [number for number , player_state in enumerate(self.__get_all_player_state__()) if player_state == 1]
        stage_return = list()
        
        stage_return = self.all_stage_func[self.current_stage](list_live_player=list_live_player,stage_return=stage_return)
        

        self.__next_stage__()
        current_stage = self.__get_current_stage() 
        
        # check current stage is dialogue
        if  self.number_comment > 0 and self.current_comment_player_number != self.end_comment_player_number:
            self.current_stage -= 1
            self.__update_comment_player_number__()

        return stage_return , current_stage


    def player_operation(self,player_number:int,operation:str, target_player_number:int, description:str,current_stage:str)->bool:
        
        
        if current_stage != str(self.round)+"-"+str(self.state)+"-"+self.all_stage[((self.current_stage-1)+len(self.all_stage)) % len(self.all_stage)] :
            return False
        
        c_stage = current_stage.split("-")[2]
        
        if c_stage == "witch" :

            use_idx = 0 if description == "poison" else 1
            self.operation[c_stage][use_idx](player_number,target_player_number)
            
        elif c_stage == "dialogue":
            self.operation[c_stage](player_number=player_number,dialogue_content=description)
        else:
            self.operation[c_stage](player_number,target_player_number)
        

        return True

    def check_player_voted_state(self)->list:
        return self.__update_current_player_voted__()

    def check_role_list(role_list:list)->bool:
        """
        return True(ok) , False(error)
        """

        role_list = [ idx for idx ,value in enumerate(role_list) for _ in range(value)]
        return role_list.count(0) == 1 and role_list.count(1) == 1 and role_list.count(6) <= 1 and  (len(role_list)-role_list.count(3)) >  (role_list.count(3)+1)

    def get_game_env(self):

        current_stage = self.all_stage[self.current_stage]
        player_state = self.__get_all_player_state__()
        camp_number = self.__get_camp_number__()

        return f"""
Stage: {self.__get_current_stage()}
Game Setting: {[f"player {key}: {value}" for key, value in self.dict_player_number_to_roles.items()]}
god number: {camp_number[0]}, village number: {camp_number[1]}, werewolf number: {camp_number[2]}
all player's state: {[f"player {idx}: {state}" for idx , state in enumerate(player_state)]}
        """


    """ Private Use func"""


    """ Stage Use func """
    def __get_current_stage(self)->str:
        if self.round == 0 :
            return "None"

        return str(self.round)+"-"+str(self.state)+"-"+self.all_stage[((self.current_stage-1)+len(self.all_stage)) % len(self.all_stage)]
    
    def __stage_werewolf__(self,list_live_player:list,stage_return:list)->list:
        
        self.__night__()
        # reset previous vote
        self.__reset_vote__()
        stage_return.append((self.__get_dict_roles_to_player_number__()["werewolf"],"vote",list_live_player,"狼人投票殺人"))
        
        return stage_return
    
    def __stage_seer__(self,list_live_player:list,stage_return:list)->list:

        self.__get_werewolf_vote_res__()
        try:
            seer_number = self.__get_dict_roles_to_player_number__()["seer"][0]
            list_live_player = self.__setting_seer_target_list__(seer_number=seer_number)
            if self.list_players[seer_number].state:
                stage_return.append(([seer_number],"vote",list_live_player,"預言家查身分"))
            
            return stage_return
        except:
            self.__next_stage__()
            return self.all_stage_func[self.current_stage](list_live_player=list_live_player,stage_return=stage_return)

    def __stage_witch__(self,list_live_player:list,stage_return:list)->list:
        
        seed_player_number =self.__get_current_seer_player__()
        seer_number = self.__get_dict_roles_to_player_number__()["seer"][0]
        
        if seer_number != None:
            if seed_player_number == None:
                list_live_player = self.__setting_seer_target_list__(seer_number=seer_number)
                self.__seer_check_identity__(seer_number,random.choice(list_live_player))
                seed_player_number =self.__get_current_seer_player__()
            if self.list_players[seer_number].state:
                stage_return.append(([seer_number],"role_info",[seed_player_number],f"{self.list_players[seed_player_number].identity}"))
        try:    
            witch_number = self.__get_dict_roles_to_player_number__()["witch"][0]
            if self.list_players[witch_number].state:
                killed_player = self.__get_current_killed_player__()

                if self.list_players[witch_number].save_times > 0 :
                    stage_return.append(([witch_number],"vote_or_not",[killed_player],"女巫救人"))
                if self.list_players[witch_number].kill_times > 0 :
                    list_live_player.insert(killed_player,killed_player)
                    stage_return.append(([witch_number],"vote_or_not",list_live_player,"女巫毒人"))    
        except:
            self.__next_stage__()
            return self.all_stage_func[self.current_stage](list_live_player=list_live_player,stage_return=stage_return)
        
        return stage_return
    
    def __stage_check_end1__(self,list_live_player:list,stage_return:list)->list:
        
        self.__day__()
        # get werewolf kill player number
        killed_player = self.__get_killed_player_by_round__(round=self.round)
        if  killed_player != None:
            stage_return.append(([killed_player],"died",[],"狼殺的人"))
            # if it's first day, the died player can comment
            if self.round == 1:
                stage_return.append(([killed_player],"dialogue",[],"遺言"))
            # if died player is hunter, he can use skill
            if self.dict_player_number_to_roles[killed_player] == "hunter":
                stage_return.append(([killed_player],"vote_or_not",list_live_player,"獵人殺人"))
                
        # get witch kill player number
        poison_player = self.__get_poisoned_player_by_round__(round=self.round)
    
        if  poison_player != None:
            stage_return.append(([poison_player],"died",[],"女巫毒的人"))
        
        # check whether end game
        end_game_res = self.__get_end_game_res__()
        if end_game_res != None: 
            stage_return.append(end_game_res)

        if len(stage_return)==0:

            self.__next_stage__()
            return self.all_stage_func[self.current_stage](list_live_player=list_live_player,stage_return=stage_return)
        
        return stage_return
    
    def __stage_check_end2__(self,list_live_player:list,stage_return:list)->list:
        
        # get hunter kill player number
        hunterKill_player = self.__get_hunterKill_player_by_round__(round=self.round)
        # if there is killed player, he can comment
        if  hunterKill_player != None:
            stage_return.append(([hunterKill_player],"died",[],"獵人殺的人"))
            stage_return.append(([hunterKill_player],"dialogue",[],"遺言"))

        # check whether end game
        end_game_res = self.__get_end_game_res__()
        if end_game_res != None: 
            stage_return.append(end_game_res)

        if len(stage_return)==0:

            self.__next_stage__()
            return self.all_stage_func[self.current_stage](list_live_player=list_live_player,stage_return=stage_return)

        return stage_return
    
    def __stage_dialogue__(self,list_live_player:list,stage_return:list)->list:
        
        # first time into dialogue stage
        if self.number_comment == 0 :
            self.__choose_comment__()
        # add dialogue of player number who has commented 
        if len(self.list_has_commented_player_number) != 0:
            player_number =self.list_has_commented_player_number[-1]
            try:
                dialogue = self.__get_player_dialogue__(player_number=player_number)[self.round]
            except:
                dialogue = ""
            stage_return.append(([player_number],"chat",[],dialogue))
        # set next commend player
        current_comment = list_live_player[self.current_comment_player_number]
        
        stage_return.append(([current_comment],"dialogue",[],"玩家發言"))
        self.number_comment -= 1
        # add to list_has_commented_player_number
        self.list_has_commented_player_number.append(current_comment)
    
        

        # reset list_has_commented_player_number
        if len(self.list_has_commented_player_number) == len(list_live_player):
            self.list_has_commented_player_number = list()
        
        return stage_return
    
    def __stage_vote1__(self,list_live_player:list,stage_return:list)->list:

        # reset previous vote
        self.__reset_vote__()
        stage_return.append((list_live_player,"vote_or_not",list_live_player,"投票階段"))
        
        return stage_return
    
    def __stage_vote2__(self,list_live_player:list,stage_return:list)->list:
        
        
        if self.__round_vote__() :
            self.__next_stage__()
            
            return self.all_stage_func[self.current_stage](list_live_player=list_live_player,stage_return=stage_return)

        # get maximum candidates
        list_candidate = self.__get_list_candidate__()
        
        # reset previous vote
        self.__reset_vote__()
        stage_return.append((list_live_player,"vote_or_not",list_candidate,"投票階段"))
        
        return stage_return
        
    def __stage_hunter2__(self,list_live_player:list,stage_return:list)->list:
        voted_player_number = self.__get_player_vote_res__()
        
        if self.dict_player_number_to_roles[voted_player_number] !="hunter":
            self.__next_stage__()
            return self.all_stage_func[self.current_stage](list_live_player=list_live_player,stage_return=stage_return)

        hunter_number = voted_player_number
        # live player
        list_live_player = self.__get_live_player_list__()
        stage_return.append(([hunter_number],"died",[],"投票結果"))
        stage_return.append(([hunter_number],"dialogue",[],"遺言"))
        stage_return.append(([hunter_number],"vote_or_not",list_live_player,"獵人殺人"))
        
        return stage_return

    def __stage_check_end3__(self,list_live_player:list,stage_return:list)->list:
        
        voted_player_number = self.__get_voted_player_by_round__(round = self.round)

        if self.dict_player_number_to_roles[voted_player_number] != "hunter":
            stage_return.append(([voted_player_number],"died",[],"投票結果"))
            stage_return.append(([voted_player_number],"dialogue",[],"遺言"))
        else :
            hunterKill_player = self.__get_hunterKill_player_by_round__(round=self.round)
            if  hunterKill_player != None:
                stage_return.append(([hunterKill_player],"died",[],"獵人殺的人"))
                stage_return.append(([hunterKill_player],"dialogue",[],"遺言"))
        
        end_game_res = self.__get_end_game_res__()

        if end_game_res != None: 
            stage_return.append(end_game_res)
        
        if len(stage_return)==0:

            self.__next_stage__()
            return self.all_stage_func[self.current_stage](list_live_player=list_live_player,stage_return=stage_return)

        return stage_return

    def __assign_roles__(self)->list():
        """
        assign game roles to players \n
        return value : \n
            list -> 分配後的角色
        """
        
        # list_assigned_roles = random.sample(self.roles , self.num_player)
        list_assigned_roles = [0,1,2,2,3,3,4] 
        list_players = [0]*self.num_player
        # create roles 
        for idx in range(self.num_player):
        
            list_players[idx] = role( self.dict_role_setting[str(list_assigned_roles[idx])])
            
            # calculate number of god, village and werewolf camp
            
            if list_players[idx].role == "village":
                self.num_village += 1
            elif list_players[idx].role == "werewolf":
                self.num_werewolf += 1
            else :
                self.num_god += 1
        
        self.list_players = list_players

        return list_assigned_roles
    
    def __next_stage__(self):
        
        self.current_stage = (self.current_stage+1) % len(self.all_stage)
        
    def __day__(self):
        """
        setting when into day
        """
        
        # become day
        self.state = 1
        
    def __night__(self):
        """
        setting when into night
        """
        
        # become night
        self.state = 0
        self.record.append(dict())
        # next round 
        self.round += 1

    def __choose_comment__(self):
        """
        choose someone to comment \n
        return value : \n
            The player number which be chosen.
        """
        list_live_player = self.__get_live_player_list__()
        self.current_comment_player_number = random.randint(1,len(list_live_player)-1)
        # list_live_player[self.current_comment_player_number] = player_number
        self.end_comment_player_number = (self.current_comment_player_number-1+len(list_live_player)%len(list_live_player))
        self.number_comment =len(list_live_player)

    def __update_comment_player_number__(self):
        """
        next comment player
        """

        list_live_player = self.__get_live_player_list__()
        self.current_comment_player_number = (self.current_comment_player_number+1) % len(list_live_player)
    
    def __kill_or_save__(self,target_player_number:int,mode:int):
        """
        kill someone or save someone \n
        target_player_number -> want to kill or save \n
        mode -> 1(save) , -1(kill)
        """

        state = 1 if mode == 1 else 0
        
        # state not change
        if self.__get_player_info__(player_number=target_player_number)["state"] == state:
            return 
        # change state
        self.list_players[target_player_number].__update_state__(state= state)

        # update number of village, werewolf, god
        if self.list_players[target_player_number].role == "village":
            self.num_village += mode
        elif self.list_players[target_player_number].role == "werewolf":
            self.num_werewolf += mode 
        else :
            self.num_god += mode
    
    def __get_dict_roles_to_player_number__(self)->dict:
        
        self.dict_roles_to_player_number = dict()
        for key , value in self.dict_player_number_to_roles.items():
            try:
                self.dict_roles_to_player_number[value].append(key)
            except:
                self.dict_roles_to_player_number[value] = list()
                self.dict_roles_to_player_number[value].append(key)

        return self.dict_roles_to_player_number

    def __get_live_player_list__(self)->list:
        return [number for number , player_state in enumerate(self.__get_all_player_state__()) if player_state == 1]

    def __check_end_game__(self)->tuple[bool,int]:
        """
        check whether end game \n
        return value: \n
            bool -> whether end game ,True(end game), False(not yet)\n
            int -> 0(bad camp win), 1(good camp win) 
        """

        
        if self.num_god <= 0 or self.num_village <= 0 :
            return True, 0
        elif self.num_werewolf <= 0:
            return True, 1
        
        return False, None
    
    def __get_end_game_res__(self)->tuple:

        final_res , who_win = self.__check_end_game__()
        if final_res:
            return ([], "end", [], "好人陣營獲勝" if who_win else "壞人陣營獲勝")
        return None
    


    """ share Vote func """

    def __player_vote__(self,player_number,want_to_vote_player_number):
        """
        people player want to vote for \n
        player_number -> 投票玩家編號 \n
        want_to_vote_player_number -> 被投票玩家編號 \n
        """

        self.list_players[player_number].__vote__(want_to_vote_player_number)

    def __update_current_player_voted__(self)->list:
        """
        update current voted player \n
        return value : \n
            list -> list of current voted
        """
        
        list_current_vote = [-1]*self.num_player
        for idx , each_player  in enumerate(self.list_players):
            list_current_vote[idx] = each_player.current_vote_player_number 
        return list_current_vote
    
    def __reset_vote__(self):
        """
        reset all player vote state \n
        """

        for each_player in self.list_players:
            each_player.current_vote_player_number = -1

    def __find_maximum_voted_candidate__(self,list_current_vote:list)->list:
        """
        找出最高票數的人 \n
        list_current_vote -> 現在投票狀態 \n
        return value : \n
            list -> 最高票數的list
        """

        dict_vote = dict(collections.Counter(list_current_vote))

        # remove -1,not voted people
        if -1 in dict_vote :
            dict_vote.pop(-1)
        
        if len(dict_vote) !=0:
            list_candidate = [key for key , value in dict_vote.items() if value == max(dict_vote.values()) ]
        else :
            list_candidate = self.__get_live_player__()

        return list_candidate


    def __random_candidate_from_maximum_candidate__(self):
        """
        從最高票的候選人中隨機挑出一個 \n
        """
        
        list_candidate = self.__get_list_candidate__()
        
        # choose one 
        list_candidate = random.sample(list_candidate,1)
        
        # day : save voted player number
        # night : save killed player number
        self.__save_record__(player_number=list_candidate[0],kind=self.state)

    def __get_list_candidate__(self)->list:
        """
        get maximum_voted_candidate
        """

        list_current_vote = self.__update_current_player_voted__()
        return self.__find_maximum_voted_candidate__(list_current_vote)
    
    """ player Vote func"""

    def __check_player_vote_state__(self,list_current_vote)->bool:
        """
        check the vote condition \n
        list_current_vote -> list of vote state [-1,-1,2,4,5,6] \n
        return value : \n
            bool -> True(all vote), False(not yet) 
        """

        # all player vote 
        if  list_current_vote.count(-1) == 0:
            return True
        # Some players haven't vote yet
        return False
    
    def __round_vote__(self)->bool:
        """
        each round the result of all player vote \n
        return value: \n
            bool -> 是否決定出一個玩家
        """

        list_current_vote = self.__update_current_player_voted__()
        list_candidate = self.__find_maximum_voted_candidate__(list_current_vote)
        
        # multiple candidate or not all werewolf vote
        if len(list_candidate) != 1 or self.__check_player_vote_state__(list_current_vote):
            return False
        
        self.__save_record__(player_number=list_candidate[0],kind=1)
        return True

    def __get_player_vote_res__(self)->int:
        
        # 確認投票狀態
        if not self.__round_vote__():
            # 但沒決定出一個人，就直接隨機挑一個
            self.__random_candidate_from_maximum_candidate__()
        
        # kill 決定的該名玩家
        voted_player = self.__get_current_voted_player__()
        self.__kill_or_save__(target_player_number=voted_player,mode=-1)
        return voted_player
    
    """ werewolf Vote func"""
    
    def __check_werewolf_vote_state__(self,list_current_vote)->bool:
        """
        check the vote condition \n
        list_current_vote -> list of vote state [-1,-1,2,4,5,6] \n
        return value : \n
            bool -> True(all vote), False(not yet) 
        """
        
        # all werewolf vote 
        if  list_current_vote.count(-1) == (self.num_god+self.num_village):
            return True
        # Some werewolf haven't vote yet
        return False 
    
    def __night_werewolf_vote__(self)->bool:
        """
        the result of all werewolf vote at night \n
        return value: \n
            bool -> 是否決定出一個玩家
        """

        list_current_vote = self.__update_current_player_voted__()
    
        list_candidate = self.__find_maximum_voted_candidate__(list_current_vote)
        # multiple candidate or not all werewolf vote
        if len(list_candidate) != 1 or not self.__check_werewolf_vote_state__(list_current_vote):
            return False

        self.__save_record__(player_number=list_candidate[0],kind=0)
        
        return True
    
    def __get_werewolf_vote_res__(self)->int:
        # 確認投票狀態
        if not self.__night_werewolf_vote__() :
            # 但沒決定出一個人，就直接從高票中挑一個
            self.__random_candidate_from_maximum_candidate__()

        # 狼決定kill該名玩家
        killed_player_number = self.__get_current_killed_player__()
        self.__kill_or_save__(target_player_number=killed_player_number,mode=-1)
        return killed_player_number
    

    """ seer func """

    def __seer_check_identity__(self,player_number:int,target_player_number:int)->int:
        """
        get player is good or bad \n
        player_number -> who want to get identity \n
        target_player_number -> target \n
        return value : \n
            The identity is good(1) or bad(0) \n
            if you get -1 , it present you cannot get the player's identity.
        """

        # you aren't seer, seer is died, the target player is died 
        if self.list_players[player_number].role != "seer" or not self.list_players[player_number].state or (not self.list_players[target_player_number].state and target_player_number != self.__get_current_killed_player__()):
            return -1
        self.__save_record__(player_number=target_player_number,kind=2)
        return self.list_players[target_player_number].identity

    def __setting_seer_target_list__(self,seer_number):
        list_live_player = self.__get_live_player_list__()
        killed_player = self.__get_current_killed_player__()
        list_live_player.insert(killed_player,killed_player)
        list_live_player.pop(seer_number)

        return list_live_player
    
    """ witch func """

    def __witch_save__(self,player_number:int,target_player_number:int)->bool:
        """
        witch save someone \n
        player_number -> who want to get identity \n
        target_player_number -> target \n
        if target_player_number is -1 -> witch didn't use \n
        return value : \n
            True -> success saving \n
            False -> failed saving
        """
        
        # you aren't witch, witch didn't use,save_times ran out , witch is died
        if  self.list_players[player_number].role != "witch" or \
            target_player_number == -1 or \
            self.list_players[player_number].save_times <= 0 or \
            not self.list_players[player_number].state:
            
            
            return False
        # save target
        self.__kill_or_save__(target_player_number=target_player_number,mode=1)
        
        # remove kill record
        self.record[self.round-1].pop(0)
        # add save record
        self.__save_record__(player_number=target_player_number,kind=4)
        
        self.list_players[player_number].save_times -= 1
        
        return True
    
    def __witch_poison__(self,player_number:int,target_player_number:int)->bool:
        """
        witch poison someone \n
        player_number -> who want to get identity \n
        target_player_number -> target \n
        if target_player_number is -1 -> witch didn't use \n
        return value : \n
            True -> success poisoning  \n
            False -> failed poisoning
        """

        current_killed_player = self.__get_current_killed_player__()
        # you aren't witch, witch is died, witch didn't use, kill_times ran out, the target player is died
        if  self.list_players[player_number].role != "witch" or \
            target_player_number == -1 or \
            self.__get_saved_player_by_round__(round=self.round) != None or \
            self.list_players[player_number].kill_times <= 0 or \
            (not self.list_players[player_number].state and current_killed_player != player_number ) or \
            (not self.list_players[target_player_number].state and current_killed_player != target_player_number):
            
            return False
        
        self.__kill_or_save__(target_player_number=target_player_number,mode=-1)
        self.__save_record__(player_number=target_player_number,kind=3)
        self.list_players[player_number].kill_times -= 1
        return True
    
    def witch_has_save(self,player_number)->bool:
        """
        check witch whether has saved times
        """
        
        if self.__get_player_info__(player_number)["save_times"] <= 0 :
            return False
        return True
    
    def witch_has_poison(self,player_number)->bool:
        """
        check witch whether has kill times
        """

        if self.__get_player_info__(player_number)["kill_times"] <= 0:
            return False
        return True
    
    """ hunter func"""

    def __hunter_kill__(self,player_number:int,target_player_number:int)->bool:
        """
        hunter kill someone \n
        player_number -> who want to get identity \n
        target_player_number -> target \n
        if target_player_number is -1 -> hunter didn't use \n
        return value : \n
            True -> success killing \n
            False -> failed killing
        """

        # you aren't hunter, hunter didn't use, kill_times ran out, the target player is died
        if  self.list_players[player_number].role != "hunter" or \
            target_player_number == -1 or \
            self.list_players[player_number].kill_times <= 0 or \
            not self.list_players[target_player_number].state :
            return False
        self.__kill_or_save__(target_player_number=target_player_number,mode=-1)
        self.__save_record__(player_number=target_player_number,kind=5)
        self.list_players[player_number].kill_times -= 1
        return True

    """ save record information """

    def __save_record__(self,player_number:int,kind:int):
        """
        save record, include kill(0), voted(1), seer(2), poison(3), save(4), hunterKill(5) \n
        player_number -> target player number \n
        kind -> kill(0), voted(1), seer(2), poison(3), save(4), hunterKill(5)
        """

        self.record[self.round-1][kind]=player_number


    """ get information """

    def __get_killed_player_by_round__(self,round:int)->int:
        """
        get kill player in specified round \n
        return value: \n
        int -> player number
        """

        try:
            return self.record[round-1][0]
        except:
            return None
        
    def __get_current_killed_player__(self)->int:
        """
        get kill player in current round \n
        return value: \n
        int -> player number
        """

        return self.__get_killed_player_by_round__(self.round)
    
    def __get_voted_player_by_round__(self,round)->int:
        """
        get voted player in specified round \n
        return value: \n
        int -> player number
        """

        try:
            return self.record[round-1][1]
        except:
            return None
    
    def __get_current_voted_player__(self)->int:
        """
        get voted player in current round \n
        return value: \n
        int -> player number
        """

        return self.__get_voted_player_by_round__(self.round)
    
    def __get_seer_player_by_round__(self,round)->int:
        """
        get seer player in specified round \n
        return value: \n
        int -> player number
        """

    
        try:
            return self.record[round-1][2]
        except:
            return None
    
    def __get_current_seer_player__(self)->int:
        """
        get seer player in current round \n
        return value: \n
        int -> player number
        """
        return self.__get_seer_player_by_round__(self.round)
        
    def __get_poisoned_player__(self)->tuple[int,int]:
        """
        get poisoned player & which round \n
        return value: \n
        int -> player number \n
        int -> which round
        """

        for round , record in enumerate(self.record):
            if 3 in record:
                return round , record[3]
        return None, None
    
    def __get_poisoned_player_by_round__(self,round)->int:
        """
        get poison player in specified round \n
        return value: \n
        int -> player number
        """

        try:
            return self.record[round-1][3]
        except:
            return None
        
    def __get_save_player__(self)->tuple[int,int]:
        """
        get save player & which round \n
        return value: \n
        int -> player number \n
        int -> which round
        """

        for round , record in enumerate(self.record):
            if 4 in record:
                return round , record[4]
        return None, None
    
    def __get_saved_player_by_round__(self,round)->int:
        """
        get poison player in specified round \n
        return value: \n
        int -> player number
        """

        try:
            return self.record[round-1][4]
        except:
            return None

    def __get_hunterKill_player_by_round__(self,round)->int:
        """
        get hunterKill player in specified round \n
        return value: \n
        int -> player number
        """

        try:
            return self.record[round-1][5]
        except:
            return None
        
    def __get_hunterKill_player__(self)->tuple[int,int]:
        """
        get hunterKill player & which round \n
        return value: \n
        int -> player number \n
        int -> which round
        """

        for round , record in enumerate(self.record):
            
            if 5 in record:
                return round , record[5]
        return None, None
    

    """ get player information func"""

    def __get_player_info__(self,player_number)->dict:
        """
        get the player all information \n
        player_number -> target player number \n
        return value : \n
            dict -> information
        """

        return vars(self.list_players[player_number])

    def __get_live_player__(self):
        return [idx for idx , state in enumerate(self.__get_all_player_state__()) if state ]

    def __get_all_player_state__(self)->list:
        """
        get the state of player number \n 
        player_number -> player number \n
        return value : \n
            int -> state, live(1), died(0)
        """ 

        return [each.state for each in self.list_players]
    
    def __get_player_dialogue__(self,player_number:int)->dict:
        """
        get dialogue of specified player 
        """

        return self.list_players[player_number].dialogues
    
    def __save_player_dialogue__(self,player_number:int,dialogue_content:str):
        """
        save dialogue of specified player \n
        format is dict
        """
        
        self.list_players[player_number].dialogues[self.round] = dialogue_content

    def __get_current_vote_player_number__(self,player_number:int):
        """
        get current vote player number
        """

        return self.list_players[player_number].current_vote_player_number
    

    """ Didn't Use """
    
    def __get_camp_number__(self)->list:
        """
        return number of village, werewolf, god \n
        [ god , village , werewolf ]
        """

        return [self.num_god,self.num_village,self.num_werewolf]
    
    
    def get_num_of_voted_player(self)->int:
        """
        get number of current vote [current vote number / total vote number] \n
        return value : \n
            int -> number of current vote
        """

        list_current_vote = self.__update_current_player_voted__()
        return self.num_player - list_current_vote.count(-1)
    

if __name__ == "__main__":

    
    
    # 分配角色
    env = env(roles=[1,1,2,2,1])
    role_list = env.start_game()
    print(role_list)
    
    # 狼人殺人
    stage , stage_name = env.stage()
    print(stage)
    env.player_operation(player_number=stage[0][0][0],operation="vote",target_player_number=6,description="",current_stage="1-0-werewolf")
    env.player_operation(player_number=stage[0][0][1],operation="vote",target_player_number=6,description="",current_stage="1-0-werewolf")

    stage , stage_name =env.stage()
    print(stage)

    print(env.__get_current_killed_player__())
    
    # 預言家查身分
    env.player_operation(player_number=0,operation="vote",target_player_number=2,description="",current_stage="1-0-seer")

    
    stage , stage_name =env.stage()
    print(stage,stage_name)
    # 女巫 救人
    # env.witch_save(player_number=stage[0][0][0], target_player_number= stage[0][2][0])
    # 女巫 毒人
    target_player_number = random.choice(stage[1][2])
    #env.player_operation(player_number=stage[1][0][0],operation="",target_player_number=5,description="save",current_stage="1-0-witch")
    env.player_operation(player_number=stage[1][0][0],operation="vote_or_not",target_player_number=5,description="poison",current_stage="1-0-witch")
    print(env.__get_all_player_state__())
    stage , stage_name =env.stage()
    print(stage,stage_name)
    
    # 獵人殺人
    stage , stage_name =env.stage()
    print(stage,stage_name)
    # if stage[0][1] == "vote_or_not":
    #     env.player_operation(player_number=stage[0][0][0],operation="vote_or_not",target_player_number=1,description="",current_stage="1-1-hunter1")
    # check end
        # stage , stage_name =env.stage()
        # print(stage,stage_name)
    
    print(env.__get_all_player_state__())
    # 對話 1
    stage , stage_name =env.stage()
    print(stage,stage_name)
    #env.player_operation(player_number=stage[-1][0][0],operation="dialogue",target_player_number=1,description="hello",current_stage="1-1-dialogue")
    
    # 對話 2
    stage , stage_name =env.stage()
    print(stage,stage_name)
    #env.player_operation(player_number=stage[-1][0][0],operation="dialogue",target_player_number=1,description="hello",current_stage="1-1-dialogue")
    # 對話 3
    stage , stage_name =env.stage()
    print(stage,stage_name)
    #env.player_operation(player_number=stage[-1][0][0],operation="dialogue",target_player_number=1,description="hello",current_stage="1-1-dialogue")
    # 對話 4
    stage , stage_name =env.stage()
    print(stage,stage_name)
    #env.player_operation(player_number=stage[-1][0][0],operation="dialogue",target_player_number=1,description="hello",current_stage="1-1-dialogue")

    # 投票
    stage , stage_name =env.stage()
    print(stage,stage_name)
    
    for player in stage[0][0]:
        if player == -2:
            env.player_operation(player_number=player,operation="vote",target_player_number=random.choice(stage[0][2]),description="",current_stage="1-1-vote1")
        
    # 確認誰投誰
    print("Stage: confirm round 1 voted state")
    for idx ,player_voted in enumerate(env.check_player_voted_state()):
        print(f"player {idx} voted player {player_voted}")
    print()
    
    stage , stage_name =env.stage()
    print(stage,stage_name)
    
    if stage[0][1] =="vote_or_not":
        for player in stage[0][0]:
            if player == -2:
                env.player_operation(player_number=player,operation="vote",target_player_number=random.choice(stage[0][2]),description="",current_stage="1-1-vote2")
            
        # 確認誰投誰
        print("Stage: confirm round 2 voted state")
        for idx ,player_voted in enumerate(env.check_player_voted_state()):
            print(f"player {idx} voted player {player_voted}")
        print()
        stage , stage_name =env.stage()
        print(stage,stage_name)
    
    print(env.__get_all_player_state__())