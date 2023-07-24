# from role import * 
import collections 
import random 
import json

class env():
    
    """
    0 : seer
    1 : witch 
    2 : village
    3 : werewolf
    4 : hunter
    """
    
    def __init__(self, state = 1, round = 1):
        
        random.seed(10955)

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


    # start game
    def start_game(self,roles:list):
        """
        check minimum player and assign roles to all players.\n
        roles -> setting of game role
        """

        # 遊戲角色配置
        self.roles = roles
        # number of player
        self.num_player = len(roles)
        
        try : 
            if self.roles.count(3) == self.num_player:
                raise
        except: 
            print("at least one good identity")
            return 
        
        
        self.list_players = self.__assign_roles__()
        

    # assign game roles to players
    def __assign_roles__(self)->list():
        
        # list_assigned_roles = random.sample(self.roles , self.num_player)
        list_assigned_roles = [0,1,2,2,3,3] 
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
        
        return list_players
    
    def choose_comment(self)->int:
        """
        choose someone to comment
        return value : \n
            The player number which be chosen.
        """

        return random.randint(0,self.num_player-1)

    def seer_check_identity(self,player_number:int,target_player_number:int)->int:
        """
        get player is good or bad \n
        player_number -> who want to get identity \n
        target_player_number -> target \n
        return value : \n
            The identity is good(1) or bad(0) \n
            if you get -1 , it present you cannot get the player's identity.
        """

        # you aren't seer, seer is died, the target player is died 
        if self.list_players[player_number].role != "seer" or not self.list_players[player_number].state or not self.list_players[target_player_number].state :
            return -1
        return self.list_players[target_player_number].identity

    def witch_save(self,player_number:int,target_player_number:int)->bool:
        """
        witch save someone \n
        player_number -> who want to get identity \n
        target_player_number -> target \n
        return value : \n
            True -> success saving
            False -> failed saving
        """

        # you aren't witch, witch is died, save_times ran out
        if self.list_players[player_number].role != "witch" or self.list_players[player_number].save_times <= 0 or not self.list_players[player_number].state :
            return False
        self.kill_or_save(target_player_number=target_player_number,mode=1)
        self.list_players[player_number].save_times -= 1
        return True
    
    def witch_poison(self,player_number:int,target_player_number:int)->bool:
        """
        witch poison someone \n
        player_number -> who want to get identity \n
        target_player_number -> target \n
        return value : \n
            True -> success poisoning
            False -> failed poisoning
        """

        # you aren't witch, witch is died, kill_times ran out, the target player is died
        if self.list_players[player_number].role != "witch" or self.list_players[player_number].kill_times <= 0 or not self.list_players[player_number].state or not self.list_players[target_player_number].state:
            return False
        self.kill_or_save(target_player_number=target_player_number,mode=-1)
        self.list_players[player_number].kill_times -= 1
        return True

    def hunter_kill(self,player_number:int,target_player_number:int)->bool:
        """
        hunter kill someone \n
        player_number -> who want to get identity \n
        target_player_number -> target \n
        return value : \n
            True -> success killing
            False -> failed killing
        
        """
        # you aren't hunter or kill_times ran out or the target player is died
        if self.list_players[player_number].role != "hunter" or self.list_players[player_number].kill_times <= 0 or not self.list_players[target_player_number].state:
            return False
        self.kill_or_save(target_player_number=target_player_number,mode=-1)
        self.list_players[player_number].kill_times -= 1
        return True

    def get_player_state(self,number:int)->int:
        return self.list_players[number].state
    
    def get_player_dialogue(self,number:int)->list:
        return self.list_players[number].dialogues
    """ werewolf func"""
    
    def __check_werewolf_vote_state__(self,list_current_vote)->bool:

        # all werewolf vote 
        if  list_current_vote.count(-1) == (self.num_god+self.num_village):
            return True
        # Some werewolf haven't vote yet
        return False 
    
    def night_werewolf_vote(self)->tuple[bool,list]:
        """
        the result of all werewolf vote at night \n
        return value: \n
            bool -> 是否決定出一個玩家 \n
            list -> 決定出的玩家是誰
        
        """

        list_current_vote = self.__setting_voted_player__()
        list_candidate = self.__find_maximum_voted_candidate__(list_current_vote)
        
        # multiple candidate or not all werewolf vote
        if len(list_candidate) != 1 or not self.__check_werewolf_vote_state__(list_current_vote):
            return False, list_candidate
        # reset vote state
        self.__reset_current_vote__()
        # get final result 
        return True, list_candidate
    
    def __find_maximum_voted_candidate__(self,list_current_vote:list)->list:

        dict_vote = collections.Counter(list_current_vote)
        list_candidate = [key for key , value in dict_vote.items() if value == max(dict_vote.values()) and key != -1]

        return list_candidate

    def majority_vote(self,list_candidate:list)->list:
        # reset vote state
        self.__reset_current_vote__()
        return random.sample(list_candidate)

    """ vote func """
    
    def player_vote(self,player_number,want_to_vote_player_number):
        """

        people player want to vote for
        player_number -> 投票玩家編號 \n
        want_to_vote_player_number -> 被投票玩家編號 \n
        
        """

        self.list_players[player_number].vote(want_to_vote_player_number)

    def __setting_voted_player__(self)->list:
        list_current_vote = [-1]*self.num_player
        for idx , each_player  in enumerate(self.list_players):
            list_current_vote[idx] = each_player.current_vote_player_number 
        return list_current_vote
    
    # get number of voted player 
    def get_num_of_voted_player(self)->int:
        list_current_vote = self.__setting_voted_player__()
        return self.num_player - list_current_vote.count(-1)
    
    def __check_player_vote_state__(self,list_current_vote)->bool:

        # all player vote 
        if  list_current_vote.count(-1) == 0:
            return True
        # Some players haven't vote yet
        return False
    
    
    def round_vote(self)->tuple[bool,list]:
        """
        each round the result of all player vote \n
        return value: \n
            bool -> 是否決定出一個玩家 \n
            list -> 決定出的玩家是誰
        
        """

        list_current_vote = self.__setting_voted_player__()
        list_candidate = self.__find_maximum_voted_candidate__(list_current_vote)
        
        # return possible candidate(multiple)
        if len(list_candidate) != 1 or self.__check_player_vote_state__(list_current_vote):
            return False, list_candidate
        # reset vote state
        self.__reset_current_vote__()
        # return possible candidate(single)
        return True, list_candidate

    def __reset_current_vote__(self):

        for each_player in self.list_players:
            each_player.current_vote_player_number = -1

    def kill_or_save(self,target_player_number:int,mode:int):
        
        self.list_players[target_player_number].__update_state__()
        if self.list_players[target_player_number].role == "village":
            self.num_village += mode
        elif self.list_players[target_player_number].role == "werewolf":
            self.num_werewolf += mode 
        else :
            self.num_god += mode

    def check_end_game(self)->tuple[bool,int]:
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
            

class role():

    def __init__(self,init_data:dict):
        
        for key , value in init_data.items():
            setattr(self ,key , value)
        # dialogues
        self.dialogues = list()
        #　live(1) or dead(0) 
        self.state =  1
        # vote player number , -1 : not yet vote
        self.current_vote_player_number = -1
        """
        basement init 
        
        num_vote : number of vote each person  
        identity_number : 角色身分
        identity : 身分好壞
        save_times : 救人次數
        kill_times : 殺人次數
        """ 

    def __update_state__(self):
        self.state = not self.state

    def __update_num_vote__(self,num_vote:int):
        self.num_vote = num_vote

    def __vote__(self,player_number:int):
        self.current_vote_player_number = player_number

"""
    6 players : 1 seer , 1 witch , 2 villages , 2 werewolves
    7 players : 1 seer , 1 witch , 1 hunter , 2 villages , 2 werewolves

"""
if __name__ == "__main__":

    env = env()
    # 分配角色
    env.start_game(roles=[0,1,2,2,3,3])
    # !!進入夜晚
    # 狼人投票殺人, call player_vote()
    env.player_vote(player_number=0,want_to_vote_player_number=1)
    # 確認投票狀態
    result , list_candidate = env.night_werewolf_vote()
    
    # 時間到
    if not result :
        # 但沒決定出一個人，就多數決
        list_candidate = env.majority_vote(list_candidate=list_candidate)
    # kill 決定的該名玩家
    killed_player = list_candidate[0]
    env.kill(killed_player)
    # 預言家查身分
    identity = env.seer_check_identity(player_number=1)
    # 女巫 救人
    env.witch_save(player_number=2, target_player_number= killed_player)
    # 女巫 毒人
    env.witch_poison(player_number=2, target_player_number= 3)
    
    # !!進入白天
    # 決定從誰發言
    start_comment_number = env.choose_comment()
    # 大家發言
    # 發言後投票 
    env.player_vote(player_number=0,want_to_vote_player_number=1)
    result , list_candidate = env.round_vote()
    # 時間到
    if not result :
        # 平票的人PK
        env.player_vote(player_number=0,want_to_vote_player_number=1)
        result , list_candidate = env.round_vote()
        # 但沒決定出一個人，就多數決
        list_candidate = env.majority_vote(list_candidate=list_candidate)
    # kill 決定的該名玩家
    killed_player = list_candidate[0]
    env.kill(killed_player)

    # 如果死的是獵人，啟動能力
    env.hunter_kill(player_number=3,target_player_number=5)
    
    # !!檢查遊戲是否結束
    final_res , who = env.check_end_game()
    if final_res:
        if who : 
            print("good camp win")
        else:
            print("bad camp win")
        # !!結束遊戲
    
    # !!循環.. 
    
    