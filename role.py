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