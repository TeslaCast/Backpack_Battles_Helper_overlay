import os
import random
from PIL import Image, ImageDraw
import time
import json
import csv
from pathlib import Path



# === Константы ===
CELL_SIZE = 160
GRID_WIDTH = 9
GRID_HEIGHT = 7
IMG_WIDTH = GRID_WIDTH * CELL_SIZE
IMG_HEIGHT = GRID_HEIGHT * CELL_SIZE

NUM_FIELDS = 100 #Количество сгенерированных картинок

# Цвета
BACKGROUND_COLOR = (168, 129, 90, 255) #Background для всего фото, приближая конечный вариант к идеалу

#Полупрозрачный квадрат для каждой ячейки
OVERLAY_COLOR = (196,176,156, 150) #Цвет полупрозрачных квадратов для каждой ячейки, как в игре
SQUARE_SIZE = 130
CORNER_RADIUS = 20

BAGS_TEMPLATE_DIR = "dataset/images/train"
ITEMS_DIR = "resized_items/items"


DATASET_DIR = "dataset"
IMAGES_DIR = "dataset/images"
TRAIN_IMAGES_DIR = "dataset/images/train"
LABELS_DIR = "dataset/labels"
TRAIN_LABELS_DIR = "dataset/labels/train"

STATS_CSV = "item_stats.csv"


# === Формы рюкзаков ===

# Формат: матрица ячеек, используемых рюкзаком
backpack_shapes = {
    "Protective Purse": [[1]],
    "Fanny Pack": [[1, 1]],
    "Stamina Sack": [[1], [1], [1]],
    "Potion Belt": [[1], [1], [1], [1]],
    "Leather Bag": [[1, 1], [1, 1]],
    "Relic Case": [[1], [1], [1], [1]],
    "Box of Prosperity": [[1, 1], [1, 1]],
    "Puzzlebag of Love": [[0, 0, 1], [1, 1, 1]],
    "Offering Bowl": [[1, 1], [1, 1]],
    "Puzzlebag of Ruin": [[1, 1, 0], [0, 1, 1]],
    "Ranger Bag": [[1, 1], [1, 1], [1, 1]],
    "Puzzlebag of Endurance": [[1, 0, 0], [1, 1, 1]],
    "Puzzlebag of Improvement": [[0, 1, 1], [1, 1, 0]],
    "Puzzlebag of Energy": [[0, 1, 0], [1, 1, 1]],
    "Storage Coffin": [[1, 1], [1, 1], [1, 1], [1, 1]],
    "Holdall": [[1, 1, 1], [1, 1, 1]],
    "Puzzlebox": [[0, 0, 1], [1, 1, 1], [0, 1, 0], [0, 1, 0]],
    "Scholar Bag": [[1, 1, 1], [1, 1, 1]],
    "Bag of Giving": [[1, 1, 1], [1, 1, 1]],
    "Duffle Bag": [[1, 1, 1], [1, 1, 1]],
    "Sewing Case": [[1, 1, 1, 1, 1], [0, 1, 1, 1, 0]],
    "Utility Pouch": [[1, 1, 1], [1, 1, 1], [1, 0, 1]],
    "Fire Pit": [[1, 1, 1], [1, 1, 1], [1, 1, 1]],
    "Vineweave Basket": [[1, 1, 1], [1, 1, 1], [1, 1, 1]],
}

# === Пути к изображениям рюкзаков ===
backpack_images = {
    name: f"resized_items/bags/{name}.png" for name in backpack_shapes
}



items_images = {
    os.path.splitext(filename)[0]: os.path.join(ITEMS_DIR, filename)
    for filename in os.listdir(ITEMS_DIR)
    if filename.endswith(".png")
}


# === Вспомогательные функции ===

def rotate_shape(shape, rotates_num=0):
    '''Функция для поворота массива различной размерности на 90 градусов по часовой стрелке'''
    
    for _ in range(rotates_num % 4):  # 4 поворота — это полный оборот, больше не нужно
        shape = [list(row) for row in zip(*shape[::-1])]
    
    return shape


def can_place(grid, shape, x, y):
    '''Функция проверяет, можно ли разместить shape в grid'''
    for dy, row in enumerate(shape):           # проходим по строкам формы
        for dx, val in enumerate(row):         # и по элементам в строке
            if val == 1:                       # если текущая ячейка непустая (1)
                gx, gy = x + dx, y + dy        # вычисляем координаты на сетке
                if gx >= GRID_WIDTH or gy >= GRID_HEIGHT or grid[gy][gx] == 1:
                    return False               # нельзя ставить: выходит за границы или ячейка занята
    return True

def place_shape(grid, shape, x, y):
    '''Заполняет ячейку grid значением 1'''
    for dy, row in enumerate(shape):
        for dx, val in enumerate(row):
            if val == 1:
                grid[y + dy][x + dx] = 1

def fill_array(val=0, grid_width = 1, grid_height = 1):
    '''Создает массив заданной размерности заполненный значением val'''
    return [[val] * grid_width for _ in range(grid_height)]

def contains_val(array, val):
    '''Проверяет, содержится ли значение val в двумерном массиве array'''
    for row in array:
        if val in row:
            return True
    return False


def print_mas(shape):
    '''Вывод двумерного массива в виде матрицы'''
    for row in shape:
        print(row)
    print()
    return 






# Проверка занятости ячеек
def is_free(occupied, x, y, w, h):
    for dy in range(h):
        for dx in range(w):
            if x + dx >= GRID_WIDTH or y + dy >= GRID_HEIGHT or occupied[y + dy][x + dx]:
                return False
    return True

# Занятие ячеек
def occupy(occupied, x, y, w, h):
    for dy in range(h):
        for dx in range(w):
            occupied[y + dy][x + dx] = True

# YOLO-аннотация
def add_yolo_annotation(txt_path, class_id, x, y, w, h):
    cx = (x + w / 2) / IMG_WIDTH
    cy = (y + h / 2) / IMG_HEIGHT
    nw = w / IMG_WIDTH
    nh = h / IMG_HEIGHT
    with open(txt_path, "a") as f:
        f.write(f"{class_id} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}\n")



os.makedirs(DATASET_DIR, exist_ok=True)

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(TRAIN_IMAGES_DIR, exist_ok=True)

os.makedirs(LABELS_DIR, exist_ok=True)
os.makedirs(TRAIN_LABELS_DIR, exist_ok=True)

# Один раз загружаем словарь из файла
with open('item_id_map.json', 'r', encoding='utf-8') as f:
    name_to_id = json.load(f)


# Загружаем подложку один раз
cell_texture = Image.open("cell.png").convert("RGBA")
cell_texture.putalpha(cell_texture.getchannel("A").point(lambda a: int(a * 0.29)))
cell_texture = cell_texture.resize((SQUARE_SIZE, SQUARE_SIZE))  # если нужно

# Подготовка статистики
item_stats = {}
item_images = {}

# Загрузка предметов
item_stats = {filename: {0: 0, 90: 0, 180: 0, 270: 0} for filename in set(items_images) | set(backpack_images)}

        


start = time.time()
#Основной цикл генерации фото количеством NUM_FIELDS
for i in range(NUM_FIELDS):
    one_iter_time = time.time()

    grid = fill_array(val=0, grid_width=GRID_WIDTH, grid_height=GRID_HEIGHT ) # Заполнение сетки GRID_WIDTHxGRID_HEIGHT значением val=0
    canvas = Image.new("RGBA", (IMG_WIDTH, IMG_HEIGHT), BACKGROUND_COLOR) #Создание основного фото с определенным цветом background
    annotations = [] #Аннотации
    placed_count = 0 #Счетчик размещенных рюкзаков
    max_attempts = 250 #Максимальное число попыток размещения

    start = time.time()
    #Попытки размещения рюкзаков
    while contains_val(array=grid, val=0):
        name = random.choice(list(backpack_shapes.keys())) #Берёт случайный ключ из словаря backpack_shapes
        base_shape = backpack_shapes[name] #Берёт значение по ключу из backpack_shapes
        img = Image.open(backpack_images[name]) # Открывает фото по ключу

        #Поворот матрицы и самого фото на случайный угол кратный 90
        rotates = random.randint(0,3)
        shape = rotate_shape(shape=base_shape, rotates_num=rotates)
        img = img.rotate(-90*rotates, expand=True)
        
        #Перевернутые координаты рюкзака
        rotated_height = len(shape)
        rotated_width = len(shape[0])      

        found = False
        for _ in range(100):
            #Случайные ячейки на поле, исключая выход за границы
            x = random.randint(0, GRID_WIDTH - rotated_width)
            y = random.randint(0, GRID_HEIGHT - rotated_height)

            #Проверка на возможность вставки
            if can_place(grid, shape, x, y):
                place_shape(grid, shape, x, y) #Меняем соответствующие ячейки grid на 1

                #Координаты для вставки отцентрованного изображения в выбранные ячейки
                box_w = rotated_width * CELL_SIZE
                box_h = rotated_height * CELL_SIZE
                paste_x = x * CELL_SIZE + (box_w - img.width) // 2
                paste_y = y * CELL_SIZE + (box_h - img.height) // 2

                #Вставка изображения 
                canvas.paste(img, (paste_x, paste_y), img)

                item_stats[name][90*rotates] += 1

                # YOLOv8 bbox
                bbox_x_center = (paste_x + img.width / 2) / IMG_WIDTH
                bbox_y_center = (paste_y + img.height / 2) / IMG_HEIGHT
                bbox_width = img.width / IMG_WIDTH
                bbox_height = img.height / IMG_HEIGHT
                class_id = name_to_id[name]  # name — это строка, например, 'Axe'

                annotations.append(f"{class_id} {bbox_x_center:.6f} {bbox_y_center:.6f} {bbox_width:.6f} {bbox_height:.6f}")
                placed_count += 1
                found = True
                break
        if not found:
            continue
    
    
    
    # Быстро вставляем подложку в каждую ячейку
    for gy in range(GRID_HEIGHT):
        for gx in range(GRID_WIDTH):
            px = gx * CELL_SIZE + (CELL_SIZE - SQUARE_SIZE) // 2
            py = gy * CELL_SIZE + (CELL_SIZE - SQUARE_SIZE) // 2
            canvas.paste(cell_texture, (px, py), cell_texture)  # маска = сам texture (RGBA)

    # Нарисовать сетку
    #TOFIX: В конце убрать сетку
    draw = ImageDraw.Draw(canvas)
    for x in range(0, IMG_WIDTH + 1, CELL_SIZE):
        draw.line([(x, 0), (x, IMG_HEIGHT)], fill=(100, 100, 100, 255), width=3)
    for y in range(0, IMG_HEIGHT + 1, CELL_SIZE):
        draw.line([(0, y), (IMG_WIDTH, y)], fill=(100, 100, 100, 255), width=3)


    occupied = fill_array(val=False, grid_width=GRID_WIDTH, grid_height=GRID_HEIGHT)

    while contains_val(array=occupied, val=False):
        name = random.choice(list(items_images.keys()))
        img = Image.open(items_images[name]) # Открывает фото по ключу


        rotates = random.randint(0,3)
        img = img.rotate(-90*rotates, expand=True)

        w_cells = img.width // CELL_SIZE
        h_cells = img.height // CELL_SIZE
        
        placed = False
        for _ in range(50):
            x = random.randint(0, GRID_WIDTH - w_cells)
            y = random.randint(0, GRID_HEIGHT - h_cells)

            if is_free(occupied, x, y, w_cells, h_cells):
                    occupy(occupied, x, y, w_cells, h_cells)

                    px = x * CELL_SIZE + (w_cells * CELL_SIZE - img.width) // 2
                    py = y * CELL_SIZE + (h_cells * CELL_SIZE - img.height) // 2
                    canvas.paste(img, (px, py), img)

                    item_stats[name][90*rotates] += 1
                    

                    # YOLOv8 bbox
                    bbox_x_center = (px + img.width / 2) / IMG_WIDTH
                    bbox_y_center = (py + img.height / 2) / IMG_HEIGHT
                    bbox_width = img.width / IMG_WIDTH
                    bbox_height = img.height / IMG_HEIGHT
                    class_id = name_to_id[name]  # name — это строка, например, 'Axe'

                    annotations.append(f"{class_id} {bbox_x_center:.6f} {bbox_y_center:.6f} {bbox_width:.6f} {bbox_height:.6f}")
                    placed = True
                    break
                    #add_yolo_annotation(label_path, class_id, px, py, img.width, img.height)
        if not placed:
            continue

    # Сохранение
    image_path = f"dataset/images/train/{i}.png"
    label_path = f"dataset/labels/train/{i}.txt"

    canvas.save(image_path)
    with open(label_path, "w") as f:
        f.write("\n".join(annotations))

    print(f"✅ Сохранено: {image_path} и {label_path} (рюкзаков: {placed_count})")

    print("Время одной итерации: ",time.time() - one_iter_time)
print("Время выполнения ",NUM_FIELDS," итераций :",time.time() - start)
# Сохранение статистики
with open(STATS_CSV, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Item", "Total", "0°", "90°", "180°", "270°"])
    for name, angles in item_stats.items():
        total = sum(angles.values())
        writer.writerow([name, total, angles[0], angles[90], angles[180], angles[270]])

print(f"\n📊 Статистика записана в {STATS_CSV}")