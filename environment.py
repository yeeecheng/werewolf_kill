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
        # role init setting
        with open("./role_setting.json") as file:
            self.dict_role_setting = json.load(file)

    # start game
    def start_game(self,roles:list):
        
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
        
        # werewolves choose who they want to kill
        # current_round_killed = self.werewolf_kill([0,1])
        
        # seer 

        # self.seer_check_identity(0)
    
        # witch
        
        # if self.num_of_poison != 0 :
        #     self.witch_poison(-1)
        
        # if self.num_of_save != 0:
        #     self.witch_save(-1)

        # # comment round

        # #　vote 
        # list_candidate = self.vote([0,0,0,1,1,1,2])
        # if len(list_candidate) != 1 :
        #     pass


    # assign game roles to players
    def __assign_roles__(self)->list():
        
        # list_assigned_roles = random.sample(self.roles , self.num_player)
        list_assigned_roles = [0,1,2,2,3,3] 
        list_players = [0]*self.num_player
        # create roles 
        for idx in range(self.num_player):
            list_players[idx] = role( self.dict_role_setting[str(list_assigned_roles[idx])])
        
        return list_players
    
    # choose someone to comment 
    def choose_comment(self)->int:
        return random.randint(0,self.num_player-1)
    
    # choose the people who is voted to maximum number 
    def vote(self,list_voted:list):

        dict_vote = collections.Counter(list_voted)
        list_candidate = [key for key , value in dict_vote.items() if value == max(dict_vote.values())]
        return list_candidate

    def werewolf_kill(self,list_want_kill:list()):
        
        dict_vote = collections.Counter(list_want_kill)

        list_candidate = [key for key , value in dict_vote.items() if value == max(dict_vote.values())]
        killed_number = 0
        if len(list_candidate) > 1:
            killed_number = random.choice(list_candidate)
            
        self.list_players[killed_number].state = 0

        return killed_number

    def seer_check_identity(self,number:int):
        return self.list_players[number].identity

    def witch_save(self,number:int):
        
        try:
            self.list_players[number].state = 1
        # -1 不救
        except:
            return 

    def witch_poison(self,number:int):
        
        try:
            self.list_players[number].state = 0
        # -1 不殺
        except:
            return

    def hunter_kill(self,number:int):
        if self.get_state(number) == 1:
            self.list_players[number].update_state()

    def get_player_state(self,number:int)->int:
        return self.list_players[number].state
    
    def get_player_dialogue(self,number:int)->list:
        return self.list_players[number].dialogues


    """ vote func """
    
    # people player want to vote for
    def player_vote(self,player_number,want_to_vote_player_number):
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
    
    def __check_vote_state__(self,list_current_vote)->bool:

        # all player vote 
        if  list_current_vote.count(-1) == 0:
            return True
        # Some players haven't vote yet
        return False
    
    def round_vote(self)->tuple[bool,list]:
        
        list_current_vote = self.__setting_voted_player__()
        if not self.__check_vote_state__(list_current_vote):
            return False, None
        
        dict_vote = collections.Counter(list_current_vote)
        list_candidate = [key for key , value in dict_vote.items() if value == max(dict_vote.values())]
        
        if len(list_candidate) != 1:
            return False, list_candidate
        
        return True, list_candidate



class role():

    def __init__(self,init_data:dict):
        
        for key , value in init_data.items():
            setattr(self ,key , value)
        # dialogues
        self.dialogues = list()
        #　live(1) or dead(0) 
        self.state =  1
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
抽角色

夜晚

狼人殺人
seer
witch

"""
"""
    6 players : 1 seer , 1 witch , 2 villages , 2 werewolves
    7 players : 1 seer , 1 witch , 1 hunter , 2 villages , 2 werewolves

"""
if __name__ == "__main__":

    env = env()
    env.start_game(roles=[0,1,2,2,3,3])
    # env.werewolf_kill([0,1,1,0])
    
    