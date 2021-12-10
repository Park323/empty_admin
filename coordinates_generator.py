import cv2 as open_cv
import numpy as np
import yaml

from math import *
from copy import deepcopy
from operator import itemgetter
from colors import *
from drawing_utils import draw_contours

class CoordinatesGenerator:
    KEY_RESET = ord("r")
    KEY_MODIFY = ord("m")
    KEY_QUIT = ord("q")
    KEY_SORT = ord("s")

    def __init__(self, image, stream, annos, color):
        self.output = []
        self.table_form = []
        self.outstream = stream
        self.caption = 'ParkingLot'
        self.color = color

        self.img_raw    = image
        self.image = image.copy()
        self.img_backup = self.image.copy()
        
        self.click_count = 0
        self.hover_flag = False
        self.hover_idx = -1
        
        self.annos = annos
        if self.annos:        
            self.ids = len(self.annos) 
            for id, anno in enumerate(self.annos):                
                self.output.append({'id':id, 'coordinates':anno, 'color':self.color})
            self.reset_drawing()
        else:
            self.ids = 0
        
        self.coordinates = []
        self.mode = 'a'
        open_cv.namedWindow(self.caption, open_cv.WINDOW_GUI_EXPANDED)
        open_cv.setMouseCallback(self.caption, self.__mouse_callback)
        
    def reset_drawing(self):
        self.image = self.img_raw.copy()
        self.print_manual()
        for obj in self.output:
            id, anno, color = obj.values()
            draw_contours(self.image, np.array(anno), str(id+1), COLOR_WHITE, color)
        self.img_backup = self.image.copy()

    def generate(self, return_data=False):
        while True:
            open_cv.imshow(self.caption, self.image)
            key = open_cv.waitKey(0)

            if key == CoordinatesGenerator.KEY_RESET:
                self.reset()
            elif key == CoordinatesGenerator.KEY_SORT:
                self.initialize_index()
                self.reset_drawing()     
            elif key == CoordinatesGenerator.KEY_QUIT:
                if not self.table_form:
                    self.table_form = [len(self.output)]
                break
        open_cv.destroyWindow(self.caption)
        
        if return_data:
            return {'table':self.table_form,
                    'pred_boxes':[obj['coordinates'] for obj in sorted(self.output, key=lambda x: x['id'])]}
        else:    
            print( {'table':self.table_form,
                    'pred_boxes':[obj['coordinates'] for obj in sorted(self.output, key=lambda x: x['id'])]} )
            for obj in self.output:
                self.outstream.write(yml_string(obj['id'], obj['coordinates']))

    def __mouse_callback(self, event, x, y, flags, params):

        if event == open_cv.EVENT_MOUSEMOVE:
            b, idx = self.isin_contours(x,y)
            if (not b or (self.hover_idx not in [idx,-1])) and self.hover_flag:
                self.hover_flag = False
                try:
                    obj = self.output[self.hover_idx]
                    draw_contours(self.image, np.array(obj['coordinates']), str(obj['id']+1), COLOR_WHITE, self.color)
                except:
                    pass
            if b:
                self.hover_flag = True
                self.hover_idx = idx
                obj = self.output[idx]
                draw_contours(self.image, np.array(obj['coordinates']), str(obj['id']+1), COLOR_WHITE, COLOR_GREEN)
        
        if event == open_cv.EVENT_MOUSEWHEEL:
            b, idx = self.isin_contours(x,y)
            if b and flags > 0 and idx < len(self.output)-1:
                self.output[idx]['id'] += 1
                self.output[idx+1]['id'] -= 1
                self.output = sorted(self.output, key=itemgetter('id'))
                self.reset_drawing()
            elif b and flags <= 0 and self.output[idx]['id'] > 0:
                self.output[idx]['id'] -= 1
                self.output[idx-1]['id'] += 1
                self.output = sorted(self.output, key=itemgetter('id'))
                self.reset_drawing()
                
        
        if event == open_cv.EVENT_RBUTTONDOWN:
            b, idx = self.isin_contours(x,y)
            if b:
                for k in range(idx, len(self.output)):
                    self.output[k]['id'] -= 1
                self.output.pop(idx)
                self.reset_drawing()
                self.ids -= 1

        if event == open_cv.EVENT_LBUTTONDOWN:
            if self.click_count==0:
                self.img_backup = self.image.copy()
            self.coordinates.append((x, y))
            self.click_count += 1

            if self.click_count >= 4:
                self.__handle_done()
                self.img_backup = self.image.copy()

            elif self.click_count > 1:
                self.__handle_click_progress()

        open_cv.imshow(self.caption, self.image)
        
    def __handle_click_progress(self):
        open_cv.line(self.image, self.coordinates[-2], self.coordinates[-1], (255, 0, 0), 1)

    def __handle_done(self):
        open_cv.line(self.image,
                     self.coordinates[2],
                     self.coordinates[3],
                     self.color,
                     1)
        open_cv.line(self.image,
                     self.coordinates[3],
                     self.coordinates[0],
                     self.color,
                     1)

        self.click_count = 0

        coordinates = np.array(self.coordinates)
        
        draw_contours(self.image, coordinates, str(self.ids + 1), COLOR_WHITE, self.color)
        
        self.output.append({'id':self.ids, 'coordinates':coordinates.tolist(), 'color':self.color})

        for i in range(0, 4):
            self.coordinates.pop()

        self.ids += 1
        
    def reset(self):
        self.image = self.img_backup.copy()
        self.coordinates = []
        self.click_count = 0
        
    def isin_contours(self, x, y):
        for idx, obj in enumerate(self.output):
            coords = obj['coordinates']
            inter_points = []
            
            for i in range(4):
                j = 0 if i==3 else i+1
                line = find_line(coords[i], coords[j])
                
                for points in line:
                    if y==points[1]:
                        inter_points.append(points[0])
                        
            if not inter_points:
                continue
            elif np.min(inter_points)<= x and np.max(inter_points)>=x:
                return True, idx
            else:
                continue
            
        return False, None
    
    def print_manual(self):
        font_scale = 0.5
        font_thickness = 1
        line_margin = 20
        texts = ['Reset : R',
                 'Sort  : S',
                 'Quit  : Q',
                 'Index : Scroll',
                 'Delete: Right Click']
        for i, text in enumerate(texts):    
            open_cv.putText(self.image,
                            text,
                            [10,25+line_margin*i],
                            open_cv.FONT_HERSHEY_SIMPLEX,
                            font_scale,
                            COLOR_GREEN,
                            font_thickness,
                            open_cv.LINE_AA)

    def initialize_index(self):
        candidates = deepcopy(self.output)
        _momentset = [open_cv.moments(np.array(coordinates)) for coordinates in [obj['coordinates'] for obj in candidates]]
        centers = [(int(moments["m10"] / moments["m00"]) - 3, int(moments["m01"] / moments["m00"]) + 3) for moments in _momentset]
        for center, candidate in zip(centers, candidates):
            candidate['center'] = center
        
        new_output = []
        self.table_form = []
        acc_idx = 0
        while candidates:
            new_coords = []
        
            candidates = sorted(candidates, key=lambda x: x['center'][1])
            candidate = candidates.pop(0)
            # print(f'\n--------------------------------------\ncandidate chosen: {candidate}')
            new_coords.append(candidate)
        
            idx = 0
            while idx < len(candidates):
                _boxes = [obj['coordinates'] for obj in new_coords]
                _centers = [obj['center'] for obj in new_coords]
                crit = np.array(_centers).mean(axis=0)
                height = (np.array(_boxes).max(axis=1)-np.array(_boxes).min(axis=1)).mean(axis=0)[1]
                
                neighbor = candidates[idx]
                y = neighbor['center'][1]
                thres = 0.4
                if y >= crit[1]-thres * height and y <= crit[1]+thres * height:
                    # print(f'\tneighbor {idx}th : {neighbor}')
                    # print(f'\tcurrent acc idx: {acc_idx}, rest candidates:{len(candidates)}')
                    new_coords.append(candidates.pop(idx))
                else:
                    idx += 1
            
            for obj in sorted(new_coords, key=lambda x: x['center'][0]):
                new_output.append({'id':acc_idx,
                                   'coordinates':obj['coordinates'],
                                   'color':self.color})
                acc_idx += 1
            
            self.table_form.append(len(new_coords))
        self.output = new_output
        
def find_line(c0:list, c1:list, thick=None, dense=256, img_size=None, finite=True, only_corner=False):
    x0, y0 = c0
    x1, y1 = c1
    
    if img_size!=None:
        H = img_size[0]
        W = img_size[1]
    else:
        H = np.Infinity
        W = np.Infinity
    
    if finite:
        ymin, ymax = (y0, y1) if y0 < y1 else (y1, y0)
        xmin, xmax = (x0, x1) if x0 < x1 else (x1, x0)
        x_bound_check = lambda x: True
        y_bound_check = lambda y: True
    else:
        ymin, ymax = 0, H-1
        xmin, xmax = 0, W-1
        x_bound_check = lambda x: xmin <= x and x <= xmax
        y_bound_check = lambda y: ymin <= y and y <= ymax
    
    if not thick:
        if y1==y0:
            result = [[x, y0] for x in range(xmin, xmax+1)]
        else:
            inverse_grad = (x1-x0)/(y1-y0)
            result = [[round((y-y0)*inverse_grad + x0), y] for y in range(ymin, ymax+1)]
    else:
        if y1==y0:
            if only_corner:
                result = [[x, y] for y in [y0-thick, y0+thick+1] for x in [xmin, xmax]]
            else:
                result = [[x, y] for y in range(y0-thick, y0+thick+1) for x in range(xmin, xmax+1)]
        elif x1==x0:
            if only_corner:
                result = [[x, y] for x in [x0-thick, x0+thick+1] for y in [ymin, ymax]]
            else:
                result = [[x, y] for x in range(x0-thick, x0+thick+1) for y in range(ymin, ymax+1)]
        else:
            inverse_grad = (x1-x0)/(y1-y0)
            t = thick * sin(atan2(-(x1-x0), (y1-y0)))
            if only_corner:
                points = [[(y-y0)*inverse_grad + x0, y] for y in [ymin, ymax]]
                result = [[round(x+t0), round(-inverse_grad*(t0)+y)] for t0 in [-abs(t), abs(t)] for x,y in points]
            else:
                points = [[(y-y0)*inverse_grad + x0, y] for y in np.linspace(ymin, ymax+1,dense)]
                result = [[round(x+t0), round(-inverse_grad*(t0)+y)] for t0 in np.linspace(-abs(t), abs(t)+1, dense) for x,y in points]
    if only_corner:
        result = [[max(min(xmax,x),xmin),max(min(ymax,y),ymin)] for x,y in result]
        return [result[0], result[1], result[3], result[2]]
    else:
        return [[x,y] for x,y in result if x_bound_check(x) and y_bound_check(y)]
        
def yml_string(id:int, coordinates:list):
    result = "-\n          id: " + str(id) + "\n          coordinates: [" +\
             "[" + str(coordinates[0][0]) + "," + str(coordinates[0][1]) + "]," +\
             "[" + str(coordinates[1][0]) + "," + str(coordinates[1][1]) + "]," +\
             "[" + str(coordinates[2][0]) + "," + str(coordinates[2][1]) + "]," +\
             "[" + str(coordinates[3][0]) + "," + str(coordinates[3][1]) + "]]\n"
    return result
