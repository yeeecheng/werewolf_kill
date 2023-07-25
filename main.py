from environment import env
import random

envi = env()
# 分配角色
dict_assigned_roles = envi.start_game(roles=[0,1,2,2,3,3])

print("\nStage: role assign")
for idx ,role in dict_assigned_roles.items():
    print(f"player {idx}({role})")
print()
final_res , who_win = envi.check_end_game()
while not final_res:
    # !!進入夜晚
    envi.night()

    envi.reset_vote()
    # 狼人投票殺人, call player_vote()
    envi.player_vote(player_number=0,want_to_vote_player_number=1)
    envi.player_vote(player_number=0,want_to_vote_player_number=2)

    # 確認誰投誰
    print("Stage: confirm voted state")
    for idx ,player_voted in envi.get_current_player_voted().items():
        print(f"player {idx} voted player {player_voted}")
    print()

    # 確認投票狀態
    result = envi.night_werewolf_vote()
    
    # 時間到
    if not result :
        # 但沒決定出一個人，就直接從高票中挑一個
        envi.random_candidate_from_maximum_candidate()

    killed_player = envi.get_current_killed_player()
    print(f"werewolf kill player {killed_player}")
    print()
    # 狼決定kill該名玩家
    envi.kill_or_save(target_player_number=killed_player,mode=-1)

    # 預言家查身分
    target_player_number = 3 
    identity = envi.seer_check_identity(player_number=0,target_player_number=target_player_number)
    print(f"The seer check player number {target_player_number} is {identity} [good(1),bad(0)]\n")

    # 女巫 救人
    target_player_number = killed_player

    # 確認女巫使否有解藥 -> 讓女巫知道誰被殺
    res = envi.witch_has_save(player_number=1)

    save_res = envi.witch_save(player_number=1, target_player_number= killed_player)
    if save_res:
        print(f"witch save player number {target_player_number}\n")
    else :
        print("witch didn't use save\n")


    # 女巫 毒人
    target_player_number = 4
    res = envi.witch_poison(player_number=1, target_player_number= target_player_number)

    if res:
        print(f"witch poison player number {target_player_number}\n")
    else :
        print("witch didn't use poison\n")

    print(f"all player state : {envi.get_all_player_state()}")
    # !!進入白天
    envi.day()
    # 公布誰被殺了
    # 如果是hunter就觸發技能
    killed_player_number = envi.get_current_killed_player()
    try:
        if dict_assigned_roles[killed_player_number] == "hunter" : 
            envi.hunter_kill(player_number= killed_player_number,target_player_number=0)
    except:
        pass

    # 決定從誰發言
    start_comment_number = envi.choose_comment()
    print(f"\nstart from player number :{start_comment_number}\n")
    # 大家發言

    envi.save_player_dialogue(player_number=start_comment_number,dialogue_content="hello")
    envi.update_comment_player_number()
    current_comment_player_number =envi.get_current_comment_player_number()

    while current_comment_player_number != start_comment_number :
        
        envi.save_player_dialogue(player_number=current_comment_player_number,dialogue_content="hello")
        envi.update_comment_player_number()
        current_comment_player_number =envi.get_current_comment_player_number()


    # 發言後投票 

    envi.reset_vote()

    all_player_state= envi.get_all_player_state()
    for player_number,state in enumerate(all_player_state):
        if state == 0:
            continue
        want_to_vote_player_number = random.randint(0,len(all_player_state)-1)
        while all_player_state[want_to_vote_player_number] == 0:
            want_to_vote_player_number = random.randint(0,len(all_player_state)-1)
        envi.player_vote(player_number=player_number,want_to_vote_player_number=want_to_vote_player_number)

    # 確認誰投誰
    print("Stage: confirm round 1 voted state")
    for idx ,player_voted in envi.get_current_player_voted().items():
        print(f"player {idx} voted player {player_voted}")
    print()

    # 確認投票狀態
    result = envi.round_vote()


    # 時間到
    if not result :
        # !!沒RESET
        # 平票的人PK
        all_player_state= envi.get_all_player_state()
        list_candidate = envi.get_list_candidate()
        envi.reset_vote()
        for player_number,state in enumerate(all_player_state):
            if state == 0:
                continue
            want_to_vote_player_number = random.choice(list_candidate)
            envi.player_vote(player_number=player_number,want_to_vote_player_number=want_to_vote_player_number)
        
        # 確認誰投誰
        print("\nStage: confirm round 2 voted state")
        for idx ,player_voted in envi.get_current_player_voted().items():
            print(f"player {idx} voted player {player_voted}")
        print()
        result = envi.round_vote()
        # 但沒決定出一個人，就直接隨機挑一個
        if not result:
            envi.random_candidate_from_maximum_candidate()
    # kill 決定的該名玩家
    voted_player = envi.get_current_voted_player()
    print(f"all player voted player {voted_player}\n")
    
    envi.kill_or_save(target_player_number=voted_player,mode=-1)

    # 如果死的是獵人，啟動能力
    if dict_assigned_roles[voted_player] == "hunter":
        envi.hunter_kill(player_number=3,target_player_number=5)

    # !!檢查遊戲是否結束
    final_res , who_win = envi.check_end_game()

    if final_res:
        if who_win : 
            print("good camp win")
        else:
            print("bad camp win")
        # !!結束遊戲

    # !!循環.. 
