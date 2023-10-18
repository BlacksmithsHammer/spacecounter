import colorsys
from PIL import Image
import os
import shutil
import multiprocessing as mp
import PySimpleGUI as sg

sizeOfPart = 300  # длина и ширина квадратов, на которые делим
sizeOfCollision = 5  # длина пересечения разделенных изображений в пикселях
fullPartSize = sizeOfPart + sizeOfCollision


def crop(name):
    shutil.rmtree('tmp_files')
    os.mkdir("tmp_files")
    shutil.rmtree('tmp_files_test')
    os.mkdir("tmp_files_test")
    shutil.rmtree('tmp_files_test_txt')
    os.mkdir("tmp_files_test_txt")

    data_to_crop = Image.open(name)

    for x in range(0, data_to_crop.width, sizeOfPart):
        for y in range(0, data_to_crop.height, sizeOfPart):
            new = Image.new(mode="RGBA", size=(fullPartSize, fullPartSize))
            pix = new.load()
            for px in range(fullPartSize):
                for py in range(fullPartSize):
                    if (px + x < data_to_crop.width and py + y < data_to_crop.height):
                        pix[px, py] = data_to_crop.getpixel((px + x, py + y))
            new.save('tmp_files/' + str(y) + '_' + str(x) + '.tif')


def check(path):
    objs_crop = []
    sample1 = Image.open(path)
    new = Image.new(mode="RGBA", size=(fullPartSize, fullPartSize))
    pix = new.load()
    for x in range(fullPartSize):
        for y in range(fullPartSize):
            pix[x, y] = sample1.getpixel((x, y))

    def get_light(i, j):
        return colorsys.rgb_to_hls(pix[i, j][0] / 255, pix[i, j][1] / 255, pix[i, j][2] / 255)[1] * 100

    def check_cross(p):
        if pix[p[0], p[1]] == (0, 0, 0, 255) or pix[p[0], p[1]] == (0, 0, 0, 0):
            return -1
        radius = 0

        p_right = p.copy()
        p_left = p.copy()
        p_up = p.copy()
        p_down = p.copy()

        while p_right[0] < fullPartSize - 1 and p_left[0] > 0 and p_up[1] > 0 and p_down[1] < fullPartSize - 1:
            if get_light(p_right[0], p_right[1]) < get_light(p_right[0] + 1, p_right[1]):   break
            if get_light(p_left[0], p_left[1]) < get_light(p_left[0] - 1, p_left[1]):       break
            if get_light(p_up[0], p_up[1]) < get_light(p_up[0], p_up[1] - 1):               break
            if get_light(p_down[0], p_down[1]) < get_light(p_down[0], p_down[1] + 1):       break
            radius += 1
            p_right[0] += 1
            p_left[0] -= 1
            p_up[1] -= 1
            p_down[1] += 1

        return radius

    absolute_pos_x = int(path.split('/')[1].split('.')[0].split('_')[1])
    absolute_pos_y = int(path.split('/')[1].split('.')[0].split('_')[0])

    for i in range(fullPartSize):
        for j in range(fullPartSize):
            if check_cross([i, j]) > 1:
                objs_crop.append(','.join([str(i + absolute_pos_x), str(j + absolute_pos_y), str(get_light(i, j))]))
                pix[i, j] = (255, 0, 0, 255)

    with open("tmp_files_test_txt/" + path.split("/")[-1].split('.')[0] + '.txt', "a") as myfile:
        myfile.write('\n'.join(objs_crop))
    new.save('tmp_files_test/' + path.split("/")[-1])
    print('wait...' + path.split("/")[-1])


if __name__ == '__main__':

    layout = [[sg.Text('Result will be in current folder, files: result.txt and absolute_number.txt')],
              [sg.Text('please, put file in current directory and write full name there\nexample: space.tif'),
               sg.InputText()],
              [sg.Button('Ok'), sg.Button('Cancel')]]
    window = sg.Window('count space objects', layout)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel':  # if user closes window or clicks cancel
            break

        crop(values[0])
        paths = os.listdir('tmp_files/')
        cores = 16
        data = [[] for _ in range(cores)]

        for i in range(0, len(paths), cores):
            for j in range(cores):
                if len(paths) > i + j:
                    data[j].append('tmp_files/' + paths[i + j])

        with mp.Pool(cores) as p:
            res = p.map_async(check, ['tmp_files/' + e for e in paths])
            res.wait()

            path_dir = 'tmp_files_test_txt/'
            filenames = os.listdir(path_dir)
            all_k = 0

            with open('result.txt', 'w') as outfile:
                for fname in filenames:
                    with open(path_dir + fname) as infile:
                        for line in infile:
                            outfile.write(line)
                            all_k += 1
                            # print(line)
                        outfile.write('\n')
            with open('absolute_number.txt', 'w') as outfile:
                outfile.write(str(all_k))
    window.close()
