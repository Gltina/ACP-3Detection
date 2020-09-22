# evaluate the trained result with standard label marked manually
# before running, please make sure
# 'trained_label' and 'standard_label' folder
# is existed in current work path

import numpy as np
import copy
import os
from interest_area import calculate_overlapping

# required before use
label_list = ['Socket', 'Plug']
standard_volume = {
    'Socket': 0,
    'Plug': 0
}

trained_path = 'C:/Users/Lei Li/OneDrive/point cloud data/PMD_datasets/Socket_3Detection/to_KITTI_evaluation/for fine detection/evaluation_250'


def get_rotation_matrix_z(theta):
    c, s = np.cos(theta), np.sin(theta)
    return np.mat([
        [c, -s, 0, 0],
        [s, c, 0, 0],
        [0, 0, 1.0, 0],
        [0, 0, 0, 1]
    ])


# return drawable_corners, rectangle_2d
# drawable_corners  : can be draw a 3D box directly
# rectangle_2d      : can be evaluated in plane of XOY
def read_from_label(res):
    # position, dimension, rotation
    x, y, z = 0, 0, 0
    dx, dy, dz = res[3] / 2, res[4] / 2, res[5] / 2
    corners = [
        [-dx, dy, -dz, 1],
        [-dx, -dy, -dz, 1],
        [dx, -dy, -dz, 1],
        [dx, dy, -dz, 1],
        [-dx, dy, dz, 1],
        [-dx, -dy, dz, 1],
        [dx, dy, dz, 1],
        [dx, -dy, dz, 1]
    ]
    # print(corners)
    corners = np.mat(corners).T

    # obtain rotation matrix
    m_r = get_rotation_matrix_z(res[6])
    # print(m_r)
    m_r[:, 3] = np.mat([res[0], res[1], res[2], 1]).reshape((4, 1))
    # print(m_r)

    # apply matrix
    corners_t = m_r * corners
    # print(corners_t.T)
    rectangle_2d = [res[1], res[0], dy * 2, dx * 2, np.rad2deg(res[6])]
    return corners_t.T, rectangle_2d


def position_dimension_rotation(KITTI_label):
    # print(KITTI_label)
    # position dimension rotation
    """
    the number in label order is different from trained label files
    label  8dz  9dx 10dy  11y 12z 13x
    x: [13]+0.27
    y: -[11]
    z: -[12]+[d8]/2
    dx: [9]
    dy: [10]
    dz: [8]
    """
    return [KITTI_label[13] + 0.27, -KITTI_label[11], -KITTI_label[12] + (KITTI_label[8] / 2),
            KITTI_label[9], KITTI_label[10], KITTI_label[8], -KITTI_label[14]]


def get_the_right_one(res_standard, res_trained):
    tar_item = None
    for t_item in res_trained:
        if res_standard[0] == t_item[0]:
            tar_item = copy.deepcopy(t_item)
            tar_item.remove(tar_item[0])
            break

    return tar_item


def get_trained_data_list():
    folder_name = trained_path
    trained_filename_list = [folder_name + '/' + filename for filename in os.listdir(folder_name)]
    train_data = []
    for filename in trained_filename_list:
        res = get_trained_data(filename)
        if res:
            train_data.append(res)
        else:
            train_data.append(res)
    return train_data


def get_standard_data_list():
    folder_name = 'standard_label'
    standard_filename_list = [folder_name + '/' + filename for filename in os.listdir(folder_name)]
    standard_data = []
    for filename in standard_filename_list:
        res = get_trained_data(filename)
        if res:
            standard_data.append(res)
    return standard_data


def get_trained_data(filename):
    with open(filename, 'r') as f:
        labels = []
        for label in f:
            values = []
            for number in label.strip().split(' '):
                if number not in label_list:
                    values.append(float(number))
                else:
                    values.append(number)
            # print(values)
            # label_number = [float(number) if number != 'Socket' else number for number in label.strip().split(' ')]
            labels.append(values)
        return labels


def get_delta_between_two_labels(standard_label, trained_label):
    position_delta_x = np.fabs(standard_label[0] - trained_label[0])
    position_delta_y = np.fabs(standard_label[1] - trained_label[1])
    position_delta_z = np.fabs(standard_label[2] - trained_label[2])

    dimension_delta_x = np.fabs(standard_label[3] - trained_label[3])
    dimension_delta_y = np.fabs(standard_label[4] - trained_label[4])
    dimension_delta_z = np.fabs(standard_label[5] - trained_label[5])

    rotation_delta = np.fabs(standard_label[6] - trained_label[6])

    return [position_delta_x, position_delta_y, position_delta_z,
            dimension_delta_x, dimension_delta_y, dimension_delta_z,
            rotation_delta]


if __name__ == '__main__':
    # get filename list
    trained_data_list = get_trained_data_list()
    standard_data_list = get_standard_data_list()

    # print(trained_data_list)
    # print(standard_data_list)

    skip_count = {key: 0 for key in label_list}
    sum_volume, volume_count = {key: 0 for key in label_list}, {key: 0 for key in label_list}

    for idx, item in enumerate(standard_data_list):
        # print('{}->{}'.format(len(item), len(trained_data_list[idx])))
        for specific_label in item:
            # print(specific_label)
            label = np.array(position_dimension_rotation(specific_label)).round(8)
            curr_label_name = specific_label[0]

            # process invalid data
            if len(trained_data_list[idx]) == 0:
                skip_count[curr_label_name] = skip_count[curr_label_name] + 1
                volume_count[curr_label_name] = volume_count[curr_label_name] + 1
                continue

            # in practice, there will be only one label in trained label file
            tar_label = get_the_right_one(specific_label, trained_data_list[idx])

            # process none label
            if tar_label is None:
                print('No {} in {}_trained'.format(curr_label_name, idx))
                skip_count[curr_label_name] = skip_count[curr_label_name] + 1
                volume_count[curr_label_name] = volume_count[curr_label_name] + 1
                continue

            tar_label = np.array(tar_label).round(8)
            # print('Now compare between\n', label, '\nand\n', tar_label)
            height = np.fabs(tar_label[5]) if np.fabs(label[5]) > np.fabs(tar_label[5]) else np.fabs(label[5])
            # print(label, tar_label)

            # standard data(marked manually)
            standard_draw_corners, standard_rectangle_2d \
                = read_from_label(label)
            # trained data
            detected_draw_corners, detected_rectangle_2d \
                = read_from_label(tar_label)
            # delta between every items
            delta_items = get_delta_between_two_labels(label, tar_label)

            # interest_area rect1_area rect2_area
            # print('Now compare between\n', standard_rectangle_2d, '\nand\n', detected_rectangle_2d)
            overlap = calculate_overlapping(standard_rectangle_2d, detected_rectangle_2d, False)
            sum_volume[curr_label_name] = sum_volume[curr_label_name] + overlap[0] * height
            volume_count[curr_label_name] = volume_count[curr_label_name] + 1
            # original volume is based on m^3
            # print('[{:03n}]\toverlap_volume({} cm^3)\toverlap({} m^3)\theight({} m)'.format(idx, round(overlap[0] * height * 1e6, 6), round(overlap[0], 6), round(height, 6)))

    for l in label_list:
        print('[{}] average volume:{} cm^3, skip count:{}'.format(l, np.fabs(sum_volume[l] / volume_count[l] * 1e6 - standard_volume[l]), skip_count[l]))
