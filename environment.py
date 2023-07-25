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
    
    def __init__(self, state = 0, round = 0):
        
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
        
        self.kill_and_save_record = list()


    # start game
    def start_game(self,roles:list)->list:
        """
        check minimum player and assign roles to all players.\n
        roles -> setting of game role \n
        return value :
            dict_assigned_roles -> {player x: 分配後的角色}
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
        
        
        list_assigned_roles = self.__assign_roles__()

        self.dict_assigned_roles = {idx:self.dict_role_setting[str(each)]["role"] for idx,each in enumerate(list_assigned_roles)}

        return self.dict_assigned_roles
        
    def __assign_roles__(self)->list():
        """
        assign game roles to players \n
        return value : \n
            list -> 分配後的角色
        """
        
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
        
        self.list_players = list_players

        return list_assigned_roles
    
    def get_dict_assigned_roles(self)->dict:
        """
        return assigned roles \n
        for example: \n
        { 0 : seer, 1 : witch, 2 : village, 3 : village, 4 : werewolf, 5 : werewolf}
        """
        
        return self.dict_assigned_roles
    
    def day(self):
        """
        setting when into day
        """
        
        # become day
        self.state = 1

    def night(self):
        """
        setting when into night
        """
        
        # become night
        self.state = 0
        self.kill_and_save_record.append(dict())
        # reset save use
        self.save_use = False
        # next round 
        self.round += 1

    def choose_comment(self)->int:
        """
        choose someone to comment \n
        return value : \n
            The player number which be chosen.
        """

        self.current_comment_player_number = random.randint(0,self.num_player-1)
        return self.current_comment_player_number
    
    def update_comment_player_number(self):
        """
        next comment player
        """

        self.current_comment_player_number = (self.current_comment_player_number+1) % self.num_player
    
    def get_current_comment_player_number(self)->int:
        """
        return current comment player number
        """
        
        return self.current_comment_player_number
    
    def kill_or_save(self,target_player_number:int,mode:int):
        """
        kill someone or save someone \n
        target_player_number -> want to kill or save \n
        mode -> 1(save) , -1(kill)
        """

        state = 1
        if mode == -1:
            state = 0
        
        # state not change
        if self.get_player_info(player_number=target_player_number)["state"] == state:
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
    
    def get_camp_number(self)->list:
        """
        return number of village, werewolf, god \n
        [ god , village , werewolf ]
        """

        return [self.num_god,self.num_village,self.num_werewolf]
    
    """ vote func """

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
        
        list_candidate = [key for key , value in dict_vote.items() if value == max(dict_vote.values()) ]

        return list_candidate

    def random_candidate_from_maximum_candidate(self):
        """
        從最高票的候選人中隨機挑出一個 \n

        """
        list_candidate = self.get_list_candidate()
        # choose one 
        list_candidate = random.sample(list_candidate,1)
        
        # day : save voted player number
        # night : save killed player number
        self.__save_record__(player_number=list_candidate[0],kind=self.state)

    def get_list_candidate(self)->list:
        """
        get maximum_voted_candidate
        """

        list_current_vote = self.__update_current_player_voted__()
        return self.__find_maximum_voted_candidate__(list_current_vote)
    
    def player_vote(self,player_number,want_to_vote_player_number):
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
    def get_current_player_voted(self)->dict:
        """
        return current player voted \n
        example : \n
        {0 : 4, 1 : 0, 2 : 5, 3 : 5, 4 : 5, 5 : 3}
        """

        list_current_vote = self.__update_current_player_voted__()
        return {idx:each for idx, each in enumerate(list_current_vote) if each != -1}
    def get_num_of_voted_player(self)->int:
        """
        get number of current vote [current vote number / total vote number] \n
        return value : \n
            int -> number of current vote
        """

        list_current_vote = self.__update_current_player_voted__()
        return self.num_player - list_current_vote.count(-1)
    
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
    

    def round_vote(self)->bool:
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

    def reset_vote(self):
        """
        reset all player vote state \n
        """

        for each_player in self.list_players:
            each_player.current_vote_player_number = -1

    """ seer func """

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

    """ witch func"""
    
    def witch_has_save(self,player_number)->bool:
        """
        check witch whether has saved times
        """
        
        if self.get_player_info(player_number)["save_times"] <= 0 :
            return False
        return True
    def witch_has_poison(self,player_number)->bool:
        """
        check witch whether has kill times
        """

        if self.get_player_info(player_number)["kill_times"] <= 0:
            return False
        return True
    
    def witch_save(self,player_number:int,target_player_number:int)->bool:
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
            
            self.save_use = False
            return False
        # save target
        self.kill_or_save(target_player_number=target_player_number,mode=1)
        
        # remove kill record
        self.kill_and_save_record[self.round-1].pop(0)
        # add save record
        self.__save_record__(player_number=target_player_number,kind=3)
        
        self.list_players[player_number].save_times -= 1
        self.save_use = True
        return True
    
    def witch_poison(self,player_number:int,target_player_number:int)->bool:
        """
        witch poison someone \n
        player_number -> who want to get identity \n
        target_player_number -> target \n
        if target_player_number is -1 -> witch didn't use \n
        return value : \n
            True -> success poisoning  \n
            False -> failed poisoning
        """

        current_killed_player = self.get_current_killed_player()
        # you aren't witch, witch is died, witch didn't use, kill_times ran out, the target player is died
        if  self.list_players[player_number].role != "witch" or \
            target_player_number == -1 or \
            self.save_use == True or \
            self.list_players[player_number].kill_times <= 0 or \
            (not self.list_players[player_number].state and current_killed_player != player_number ) or \
            (not self.list_players[target_player_number].state and current_killed_player != target_player_number):
            
            return False
        
        self.kill_or_save(target_player_number=target_player_number,mode=-1)
        self.__save_record__(player_number=target_player_number,kind=2)
        self.list_players[player_number].kill_times -= 1
        return True

    """ hunter func"""

    def hunter_kill(self,player_number:int,target_player_number:int)->bool:
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
        if self.list_players[player_number].role != "hunter" or target_player_number == -1 or self.list_players[player_number].kill_times <= 0 or not self.list_players[target_player_number].state or not self.list_players[player_number].state:
            return False
        self.kill_or_save(target_player_number=target_player_number,mode=-1)
        self.__save_record__(player_number=target_player_number,kind=4)
        self.list_players[player_number].kill_times -= 1
        return True

    """ werewolf func"""
    
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
    
    def night_werewolf_vote(self)->bool:
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
    
    def __save_record__(self,player_number:int,kind:int):
        """
        save record, include kill(0), voted(1), poison(2), save(3), hunterKill(4) \n
        player_number -> target player number \n
        kind -> kill(0), voted(1), poison(2), save(3), hunterKill(4)
        """

        self.kill_and_save_record[self.round-1][kind]=player_number

    def get_killed_player_by_round(self,round:int)->int:
        """
        get kill player in specified round \n
        return value: \n
        int -> player number
        """

        try:
            return self.kill_and_save_record[round-1][0]
        except:
            return None
        
    def get_current_killed_player(self)->int:
        """
        get kill player in current round \n
        return value: \n
        int -> player number
        """

        return self.get_killed_player_by_round(self.round)
    
    def get_voted_player_by_round(self,round)->int:
        """
        get voted player in specified round \n
        return value: \n
        int -> player number
        """

        try:
            return self.kill_and_save_record[round-1][1]
        except:
            return None
    
    def get_current_voted_player(self)->int:
        """
        get voted player in current round \n
        return value: \n
        int -> player number
        """

        return self.get_voted_player_by_round(self.round)
    
    def get_poisoned_player(self)->tuple[int,int]:
        """
        get poisoned player & which round \n
        return value: \n
        int -> player number
        int -> which round
        """

        for round , record in enumerate(self.kill_and_save_record):
            if record.get(2) != None:
                return round , record[2]
        return None
    
    def get_save_player(self)->tuple[int,int]:
        """
        get save player & which round \n
        return value: \n
        int -> player number
        int -> which round
        """

        for round , record in enumerate(self.kill_and_save_record):
            if record.get(3) != None:
                return round , record[3]
        return None
    
    def get_hunterKill_player(self)->tuple[int,int]:
        """
        get hunterKill player & which round \n
        return value: \n
        int -> player number
        int -> which round
        """

        for round , record in enumerate(self.kill_and_save_record):
            if record.get(4) != None:
                return round , record[4]
        return None

    """ get player information func"""

    def get_player_info(self,player_number)->dict:
        """
        get the player all information \n
        player_number -> target player number \n
        return value :
            dict -> information
        """

        return vars(self.list_players[player_number])

    def get_all_player_state(self)->list:
        """
        get the state of player number \n 
        player_number -> player number \n
        return value : \n
            int -> state, live(1), died(0)
        """ 

        return [each.state for each in self.list_players]
    
    def get_player_dialogue(self,player_number:int)->dict:
        """
        get dialogue of specified player 
        """

        return self.list_players[player_number].dialogues
    
    def save_player_dialogue(self,player_number:int,dialogue_content:str):
        """
        save dialogue of specified player \n
        format is dict
        """

        self.list_players[player_number].dialogues[self.round] = dialogue_content
    
    def get_current_vote_player_number(self,player_number:int):
        """
        get current vote player number
        """

        return self.list_players[player_number].current_vote_player_number

class role():

    def __init__(self,init_data:dict):
        
        for key , value in init_data.items():
            setattr(self ,key , value)
        # dialogues
        self.dialogues = dict()
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

    def __update_state__(self,state):
        self.state = state

    def __update_num_vote__(self,num_vote:int):
        self.num_vote = num_vote

    def __vote__(self,player_number:int):
        self.current_vote_player_number = player_number

if __name__ == "__main__":

    
    
    env = env()
    # 分配角色
    # env.start_game(roles=[0,1,2,2,3,3])

    # info = env.get_player_info(player_number=1)
