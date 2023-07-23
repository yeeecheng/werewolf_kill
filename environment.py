# from role import * 
import random 
import collections 
class env():
    
    """
    0 : seer
    1 : witch 
    2 : village
    3 : werewolf
    4 : hunter
    """
    
    def __init__(self):
        
        random.seed(10955)

        # env's state, night(0) and day(1)
        self.state = 1
        # game current round
        self.round = 1

        self.num_of_poison = 1
        self.num_of_save =1
    

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
        
        
        self.list_players = self.assign_roles()
        
        # werewolves choose who they want to kill
        current_round_killed = self.werewolf_kill([0,1])
        
        # seer 

        self.seer_check_identity(0)
    
        # witch
        
        if self.num_of_poison != 0 :
            self.witch_poison(-1)
        
        if self.num_of_save != 0:
            self.witch_save(-1)

        # comment round

        #　vote 
        list_candidate = self.vote([0,0,0,1,1,1,2])
        if len(list_candidate) != 1 :
            pass


    # assign game roles to players
    def assign_roles(self)->list():
        
        # list_assigned_roles = random.sample(self.roles , self.num_player)
        list_assigned_roles = [0,1,2,2,3,3] 
        list_players = [role()]*self.num_player
        # create roles 
        for idx in range(self.num_player):
            list_players[idx].setting_identity(list_assigned_roles[idx])

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
        self.list_players[number].state = 0

    def get_state(self,number):
        return self.list_players[number].state
    
    def get_dialogue(self,number):
        return self.list_players[number].dialogues
        
class role():

    def __init__(self):
        
        # number of vote each person 
        self.num_vote = 1
        # live(1) or dead(0) 
        self.state = 1
        # dialogues
        self.dialogues = list()

    def setting_identity(self,identity_number):
        
        # identity, good(1) or bad(0)
        self.identity = 1
        if identity_number == 3:
            self.identity = 0

   


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
    env.werewolf_kill([0,1,1,0])
    
    