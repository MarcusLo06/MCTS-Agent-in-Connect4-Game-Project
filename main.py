import sys, pygame, random
import asyncio
from queue import Queue
from pygame.math import Vector2
from classes.tile import Tile
from classes.tilemap import TileMap
from classes.uiButton import UIButton
from helpers.pixelTranslate import translatePixelToCoordinate
from helpers.customTextRender import render_text_with_outline
from helpers.assetsGetter import get_pixels_font, get_profile_icon
from customEnums import TileState, GameState
from classes.MCTS import MCTSNode, mcts_search, free_mcts_memory


from settings import WIDTH, HEIGHT, FPS, BG, ROWS, COLUMNS, TOPBARHEIGHT, TOPBARCOLOR, FOOTERHEIGHT
    


async def game_scene(screen, clock, playbutton):
    tileSize = Vector2(WIDTH // COLUMNS, (HEIGHT) // ROWS)
    tileMap = TileMap(screen, ROWS, COLUMNS, TOPBARHEIGHT, FOOTERHEIGHT, tileSize)

    for i in range(tileMap.rows):
        for j in range(tileMap.columns):
            tileMap.initTile((i, j), TileState.NONE, 2)

    announceFont = pygame.font.Font(get_pixels_font() , 50)
    infoFont = pygame.font.Font(get_pixels_font() , 25)
    statisticFont = pygame.font.Font(get_pixels_font() , 18)
    ucbscoreFont = pygame.font.Font(get_pixels_font() , 22)

    btnFont = pygame.font.Font(get_pixels_font() , 16)
    red_player_btn = UIButton(70, 50, 50, 50, (255, 0, 0), btnFont, image_path=get_profile_icon(TileState.RED))
    blue_player_btn = UIButton(WIDTH - 70, 50, 50, 50, (255, 0, 0), btnFont, image_path=get_profile_icon(TileState.BLUE))

    
    running = True
    debug = False
    processing = False
    turn_no = 0
    mcts_iterations = 500

    red_is_robot = False
    blue_is_robot = False

    ai_task = None

    columns_stats: dict[int,dict] = {}
    ucb_score: float = 0.0
    ai_move: Vector2 = None


    async def reset_game():
        await game_scene(screen, clock, playbutton)
        # print("restarting")
        # tileMap.reset()

    async def toggle_red_player():
        nonlocal red_is_robot, red_player_btn
        if tileMap.turn == TileState.RED and processing: return
        red_is_robot = not red_is_robot
        red_player_btn.image_path = get_profile_icon(TileState.RED, red_is_robot)
        red_player_btn.refresh_image()


    async def toggle_blue_player():
        nonlocal blue_is_robot, blue_player_btn
        if tileMap.turn == TileState.BLUE and processing: return
        blue_is_robot = not blue_is_robot
        blue_player_btn.image_path = get_profile_icon(TileState.BLUE, blue_is_robot)
        blue_player_btn.refresh_image()
        


    playbutton.on_click = reset_game
    red_player_btn.on_click = toggle_red_player
    blue_player_btn.on_click = toggle_blue_player

    while running:
        dt = clock.tick(FPS) / 1000.0
        fps = clock.get_fps()

        target = pygame.mouse.get_pos()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False   

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_e:
                    debug = not debug
                    
            if tileMap.state != GameState.PLAYING:
                await playbutton.handle_event(e)

                
            else:
                await red_player_btn.handle_event(e)
                await blue_player_btn.handle_event(e)
            
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_SPACE:
                        ai_move, columns_stats, ucb_score = asyncio.create_task(mcts_search(tileMap, tileMap.turn, iterations=mcts_iterations))

                        if ai_move is not None:
                            tileMap.place_at_columns(ai_move)



                if e.type == pygame.MOUSEBUTTONDOWN:
                    if (red_is_robot and tileMap.turn == TileState.RED) or (blue_is_robot and tileMap.turn == TileState.BLUE): continue

                    arrive_target = pygame.mouse.get_pos()
                    arrive_target = Vector2(arrive_target) - Vector2(0, TOPBARHEIGHT)
                    arrive_coordinate = translatePixelToCoordinate(arrive_target, tileSize)
                    if tileMap.place_at_columns(arrive_coordinate):
                        turn_no += 1


        # AI autoplay function calling
        if tileMap.state == GameState.PLAYING:
            if (red_is_robot and tileMap.turn == TileState.RED) or (blue_is_robot and tileMap.turn == TileState.BLUE):
                # 1. Start thinking if not already thinking

                if not processing:
                    processing = True
                    # Clone before sending to background thread
                    board_snapshot = tileMap.clone()
                    # await run_mcts_worker(board_snapshot, tileMap.turn, mcts_iterations, ai_queue)
                    ai_task = asyncio.create_task(mcts_search(board_snapshot, tileMap.turn, iterations=mcts_iterations))

                # 2. Check if the thread finished
                elif processing and ai_task is not None and ai_task.done():
                    ai_move, columns_stats, ucb_score = ai_task.result()
                    if ai_move is not None:
                        if tileMap.place_at_columns(ai_move):
                            turn_no += 1
                    
                    processing = False


        # update UCB Score
        if ai_move and columns_stats and ucb_score:
            lastest_tile = tileMap.tilesDictionary[tuple(ai_move)]
            lastest_tile.ucb_score = ucb_score
            lastest_tile.winrate = columns_stats[ai_move[0]]["win_rate"]

        
        screen.fill(BG)
        topBarRect = pygame.Rect(0,0,WIDTH,TOPBARHEIGHT - 10)
        pygame.draw.rect(screen, TOPBARCOLOR, topBarRect)

        # texts
        if tileMap.state == GameState.PLAYING:
            color_turn = tileMap.turn
            announceText = "" +  color_turn.name + " turn"
            if color_turn == TileState.RED:
                announceColor = (255, 100, 100)
            elif color_turn == TileState.BLUE:
                announceColor = (100, 100, 255)
        elif tileMap.state == GameState.REDWIN:
            announceText = "Red Win"
            announceColor = (255, 200, 200)
        elif tileMap.state == GameState.BLUEWIN:
            announceText = "Blue Win"
            announceColor = (200, 200, 255)
        elif tileMap.state == GameState.DRAW:
            announceText = "Draw"
            announceColor = (100, 100, 100)


        tileMap.draw(debug)

        announceLabel = render_text_with_outline(
            fontType=announceFont,
            text=announceText,
            color=announceColor,
        )

        announceLabel_rect = announceLabel.get_rect(center = Vector2(topBarRect.centerx, TOPBARHEIGHT // 2))
        screen.blit(announceLabel, announceLabel_rect)

        infoText = "Turn " + str(turn_no) + (" - Agent is thinking.." if processing else "")

        infoLabel = render_text_with_outline(
            fontType=infoFont,
            text=infoText,
            color=(255,255,255),
        )
        infoLabel_rect = infoLabel.get_rect(center = Vector2(topBarRect.centerx, TOPBARHEIGHT * 3/4))
        screen.blit(infoLabel, infoLabel_rect)


        # hover dot place preview
        if TOPBARHEIGHT <= target[1] < HEIGHT + TOPBARHEIGHT and not((red_is_robot and tileMap.turn == TileState.RED) or (blue_is_robot and tileMap.turn == TileState.BLUE)):
            target_coordinate = translatePixelToCoordinate(target, tileSize)
            tileMap.update_preview_column(target_coordinate)
        else:
            tileMap.update_preview_column(Vector2(-1, -1))

        
        if debug:
            for i in range(COLUMNS):
                if not columns_stats or i not in columns_stats or not columns_stats[i]:
                    continue

                stat_col = columns_stats[i]
                visits = stat_col["visits"]
                winrate = stat_col["win_rate"]

                if visits > 0:
                    text_color = (int(255 * (1.0 - winrate)), int(255 * winrate), 0)
                else:
                    text_color = (255, 255, 255)

                visit_label = render_text_with_outline(
                    fontType=statisticFont,
                    text=f"{int(visits)}",
                    color=text_color
                )

                winrate_label = render_text_with_outline(
                    fontType=statisticFont,
                    text=f"{winrate * 100:.1f}%",
                    color=text_color
                )


                center_pos = Vector2(tileSize.x * i + tileSize.x / 2, TOPBARHEIGHT + HEIGHT)

                winrateLabel_rect = winrate_label.get_rect(center = center_pos + Vector2(0, FOOTERHEIGHT * 1/4))
                screen.blit(winrate_label, winrateLabel_rect)

                visitLabel_rect = visit_label.get_rect(center = center_pos + Vector2(0, FOOTERHEIGHT * 3/4))
                screen.blit(visit_label, visitLabel_rect)
        else:
            tips_label = render_text_with_outline(
                fontType=statisticFont,
                text="E: Toggle Debug, Space: Let Agent Play 1 Move",
                color=(255,255,255)
            )
            tipsLabel_rect = tips_label.get_rect(center = Vector2(WIDTH // 2, TOPBARHEIGHT + HEIGHT + FOOTERHEIGHT * 2/4))
            screen.blit(tips_label, tipsLabel_rect)


        

        # restart game button
        if tileMap.state != GameState.PLAYING:
            playbutton.draw(screen)
        else:
            red_player_btn.draw(screen)
            blue_player_btn.draw(screen)

        await asyncio.sleep(0)


        pygame.display.flip()

    pygame.quit()
    sys.exit(0)

async def main():
    pygame.init()
    pygame.display.set_caption("MCTS Agents in Connect4")

    screen = pygame.display.set_mode((WIDTH,HEIGHT + FOOTERHEIGHT + TOPBARHEIGHT))
    clock = pygame.time.Clock()

    playFont = pygame.font.Font(get_pixels_font() , 22)
    play_button = UIButton(WIDTH // 2, TOPBARHEIGHT + (HEIGHT // 2), 120, 50, (0, 200, 0), playFont, "Restart", (255, 255, 255))

    await game_scene(screen, clock, play_button)


if __name__ == "__main__":
    asyncio.run(main())

