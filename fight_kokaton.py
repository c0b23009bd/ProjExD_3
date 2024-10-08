import os
import random
import sys
import time
import math
import pygame as pg


# ゲームウィンドウの幅と高さ
WIDTH = 1100
HEIGHT = 650
NUM_OF_BOMBS = 5  # 爆弾の個数

# ディレクトリの設定
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
    imgs = {  # 0度から反時計回りに定義
        (+5, 0): img,  # 右
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  # 右下
    }

    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数 xy：こうかとん画像の初期位置座標タプル
        """
        self.img = __class__.imgs[(+5, 0)]  # デフォルトは右向き
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+5, 0)  # 初期方向を右向きに設定

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)  # 合計移動量に応じて向きを更新
            self.img = __class__.imgs[self.dire]
        screen.blit(self.img, self.rct)


class Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__(self, bird: "Bird"):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん（Birdインスタンス）
        """
        self.img = pg.image.load("fig/beam.png")  # ビームSurface
        # こうかとんの向きに応じてビームの初期速度を設定
        self.vx, self.vy = bird.dire  
        # 向いている方向の角度を計算し、ビームを回転させる
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.img = pg.transform.rotozoom(self.img, angle, 1.0)
        self.rct = self.img.get_rect()
        # こうかとんの向きに応じてビームの初期位置を設定
        self.rct.centerx = bird.rct.centerx + bird.rct.width * self.vx / 5
        self.rct.centery = bird.rct.centery + bird.rct.height * self.vy / 5

    def update(self, screen: pg.Surface):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        if check_bound(self.rct) == (True, True):
            self.rct.move_ip(self.vx, self.vy)
            screen.blit(self.img, self.rct)      


class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int):
        """
        引数に基づき爆弾円Surfaceを生成する
        引数1 color：爆弾円の色タプル
        引数2 rad：爆弾円の半径
        """
        self.img = pg.Surface((2*rad, 2*rad))  # 新しい画像オブジェクトを作成
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = +5, +5 

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


class score:
    def __init__(self):
        """ スコアを管理し、画面に表示するためのクラス """
        self.fonto = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)  # 日本語フォント
        self.color = (0, 0, 255)  # 青色
        self.score = 0  # スコアの初期値
        self.update()  # 初期スコアのSurfaceを生成

    def update(self):
        """ スコアを更新し、表示用の文字列Surfaceを生成する """
        self.img = self.fonto.render(f"スコア: {self.score}", True, self.color)
        self.rect = self.img.get_rect()
        self.rect.bottomleft = (100, HEIGHT - 50)  # 画面左下にスコアを表示

    def draw(self, screen: pg.Surface):
        """ スコアを画面に描画する """
        screen.blit(self.img, self.rect)

    def increase(self, points: int = 1):
        """ スコアを指定された点数だけ増やす (デフォルト1点) """
        self.score += points
        self.update()  # スコアを更新


class Explosion:
    """
    爆発エフェクトを管理するクラス
    """
    def __init__(self, bomb_rct: pg.Rect, life: int = 20):
        """
        爆発の初期化
        引数 bomb_rct：爆発位置を決めるための爆弾のRect
        引数 life：爆発の表示時間（デフォルトは20フレーム）
        """
        # 元の爆発画像とフリップしたものを読み込む
        self.images = [
            pg.image.load("fig/explosion.gif"),  # オリジナルの爆発画像
            pg.transform.flip(pg.image.load("fig/explosion.gif"), True, True)  # 上下左右に反転したもの
        ]
        self.index = 0  # 現在表示する画像のインデックス
        self.rct = self.images[0].get_rect(center=bomb_rct.center)  # 爆弾の位置に爆発の中心を設定
        self.life = life  # 爆発の表示時間

    def update(self, screen: pg.Surface):
        """
        爆発を描画する
        引数 screen：画面Surface
        """
        if self.life > 0:
            screen.blit(self.images[self.index // 10], self.rct)  # 画像を交互に表示
            self.index = (self.index + 1) % 20  # 画像を交互に切り替え
            self.life -= 1  # 残り時間を減少




def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    beams = []  # 複数ビームを格納するリスト
    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]
    explosions = []  # 爆発エフェクトのリスト
    clock = pg.time.Clock()
    tmr = 0
    
    # スコアクラスのインスタンスを生成
    score_keeper = score()

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                # スペースキー押下でBeamクラスのインスタンス生成
                beams.append(Beam(bird))  # 複数ビームをリストに追加
          
        screen.blit(bg_img, [0, 0])
        
        # こうかとんと爆弾の衝突判定
        for bomb in bombs:
            if bird.rct.colliderect(bomb.rct):
                bird.change_img(8, screen)
                fonto = pg.font.Font(None, 80)
                txt = fonto.render("Game Over", True, (255, 0, 0))
                screen.blit(txt, [WIDTH//2-150, HEIGHT//2])
                pg.display.update()
                time.sleep(5)
                return
        
        # ビームと爆弾の衝突判定
        for beam in beams:
            if beam is not None:  # ビームが存在する場合
                for j, bomb in enumerate(bombs):
                    if bomb is not None and beam.rct.colliderect(bomb.rct):  # ビームと爆弾が衝突したら
                        beams[beams.index(beam)] = None  # 衝突したビームをNoneに
                        bombs[j] = None  # 衝突した爆弾をNoneに
                        bird.change_img(6, screen)
                        score_keeper.increase()  # スコアを1点増加
                        explosions.append(Explosion(bomb.rct))  # 爆発エフェクトを追加
                        pg.display.update()
            
        # ビームのリストを更新（画面外に出たビームやNoneのビームを削除）
        beams = [beam for beam in beams if beam is not None and check_bound(beam.rct) == (True, True)]
        bombs = [bomb for bomb in bombs if bomb is not None]

        # こうかとんの移動
        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)

        # 各ビームの更新・描画
        for beam in beams:
            if beam is not None:
                beam.update(screen) 

        # 爆弾の更新・描画
        for bomb in bombs:
            bomb.update(screen)

        # 爆発エフェクトの更新・描画
        explosions = [explosion for explosion in explosions if explosion.life > 0]
        for explosion in explosions:
            explosion.update(screen)

        # スコアを描画     
        score_keeper.draw(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()