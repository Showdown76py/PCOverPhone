while True:
    try:
        import pygetwindow 
        import pyautogui
        import pytesseract
        from PIL import ImageGrab
        import difflib
        import numpy as np
        from pytesseract import Output
        try:
            import cv2
        except:
            print('Attention, il se peut que OpenCV ne fonctionne pas après l\'installation - suivre ces instructions jusqu\'à l\'étape 3 incluse : https://learnopencv.com/install-opencv3-on-windows/')
            raise ImportError('opencv')
        from PIL import Image
        print('Élements importés avec succès.')
        break
    except ImportError:
        import os
        os.system(input('Il manque des imports. - exécutez la commande pour installer les requirements, par défaut : pip install -r requirements.txt\n'+ '> '))
        continue

# class API_v2:
    def __init__(self) -> None:
        self.save_path = 'beta-tmpsc.png' 
        self.save_path2 = 'beta-tmpsc_plus.png' 
        self.processus = 'Sans titre - Paint'

    def getAllData(self, type='full', find=None) -> dict:
        window = pygetwindow.getWindowsWithTitle(self.processus)[0]
        x1 = window.left
        if type == 'full':     y1 = window.top
        elif type == 'bottom': y1 = window.top + (window.bottom / 1.15)
        height = window.height
        width = window.width
        x2 = x1 + width
        y2 = window.top + height
        if type == 'full':     save_path = 'beta-tmpsc.png'
        elif type == 'bottom': save_path = 'beta-tmpsc_plus.png'
        pyautogui.screenshot(save_path)
        screen = Image.open(save_path)
        screen = screen.crop((x1,y1,x2,y2))
        screen.save(save_path)
        cap = screen.convert('L')   # make grayscale
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'
        data=pytesseract.image_to_boxes(cap,output_type=Output.DICT)
        
        if find is None:
            return data
        else:
            f = find
            i = -1
            d = data['char']
            for c in data['char']:
                i += 1
                if c == f[0]:
                    t = ''
                    left_pos = 0
                    top_pos = 0
                    for _ in range(i, len(f)+i):
                        try:
                            t += d[_]
                            left_pos  = data['left'][_]
                            top_pos  = data['top'][_]
                        except: pass
                    print(t)
                    if t.startswith(f): return [t, left_pos, top_pos]



class API:
    def __init__(self) -> None:
        self.save_path = 'tmpsc.png' 
        self.save_path2 = 'tmpsc_plus.png' 
        self.processus = 'Bus Simulator 21'

    def rescaleImage(self, path, multiplier=1.5) -> str:
        img = cv2.imread(path)
        res = cv2.resize(img, dsize=(int(img.shape[1]*multiplier), int(img.shape[0]*multiplier)), interpolation=cv2.INTER_CUBIC)

        Image.fromarray(res).save(path)
        return path
    def screenshot_kmh(self) -> str:
        window = pygetwindow.getWindowsWithTitle(self.processus)[0]
        # x1 = window.left
        x1 = window.left+50
        # y1 = window.top
        y1 = window.top + (window.bottom / 1.15)
        height = window.height-70
        width = window.width
        x2 = x1 + width - (window.right / 1.10)
        y2 = (window.top + height)
        save_path = 'tmpsc_kmh.png'
        pyautogui.screenshot(save_path)
        im = Image.open(save_path)
        im = im.crop((x1,y1,x2,y2))
        im = im.convert("L")
        im.save(save_path)
        return save_path
    def screenshot(self, type='full') -> str:
        window = pygetwindow.getWindowsWithTitle(self.processus)[0]
        x1 = window.left
        if type == 'full':     y1 = window.top
        elif type == 'bottom': y1 = window.top + (window.bottom / 1.15)
        height = window.height
        width = window.width
        x2 = x1 + width
        y2 = window.top + height
        if type == 'full':     save_path = 'tmpsc.png'
        elif type == 'bottom': save_path = 'tmpsc_plus.png'
        pyautogui.screenshot(save_path)
        im = Image.open(save_path)
        im = im.crop((x1,y1,x2,y2))
        im.save(save_path)
        return save_path
    def filterText(self, text) -> list:
        passages = []
        for line in text.split('\n'):
            if len(line) > 3:
                errors = [
                    "This looks like an invalid email address. Try again?",
                    "Sorry, something's not right.",
                    "Please try again.",
                    "The email or password you entered isn't right.",
                    "As a reminder your password contains:",
                    "ABC | abc | 123 | !@% | at least 8 characters"
                ]
                # elif category == 2:
                #     errors = [
                #         'SIGN OUT'
                #     ]
                matches = difflib.get_close_matches(line, errors)
                passages.extend(matches)
        return passages
    def filterText_v2(self, text, category: int=2) -> list:
        passages = []
        for line in text.replace('\\n', '\n').split('\n'):
            if len(line) > 1:
                if category == 1:
                    errors = [f'{_}km/h' for _ in range(0, 150)]
                    errors.remove('9km/h')
                    errors.append('Okm/h')
                elif category == 2:
                    errors = [f'! {_}km/h !' for _ in range(0, 150)]
                    errors.remove('! 9km/h !')
                    errors.append('! Okm/h !')
                
                matches = difflib.get_close_matches(line, errors, cutoff=0.4)
                if len(matches) > 0:
                    # passages[text] = matches
                    passages.append(matches[0].replace('Okm/h', '0km/h'))
                
        return passages


    def read_text(self, path) -> str:
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'
        return pytesseract.image_to_string(path)
    
    def read_text_wpositions(self, type_='full') -> str:
        rgb = cv2.cvtColor(cv2.imread(self.save_path if type_ == 'full' else self.save_path2), cv2.COLOR_BGR2RGB)
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'
        return pytesseract.image_to_data(rgb, output_type=Output.DICT)