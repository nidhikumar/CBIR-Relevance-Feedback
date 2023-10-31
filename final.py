import tkinter as tk
from tkinter import Scrollbar, filedialog
import math
import os
import sys
from tkinter import messagebox
from PixInfo import PixInfo
from PIL import Image, ImageTk
import numpy as np
from sklearn import preprocessing
from statistics import stdev 
import re
ANTIALIAS = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.ANTIALIAS

# Main app.
class ImageViewer(tk.Frame):

    # Constructor.
    def __init__(self, master, pixInfo):

        tk.Frame.__init__(self, master)
        self.master = master
        self.pixInfo = pixInfo
        self.colorCode = pixInfo.get_colorCode()
        self.intenCode = pixInfo.get_intenCode()
        self.folderPath = pixInfo.get_folderPath()
        # Full-sized images.
        self.imageList = pixInfo.get_imageList()
        # Thumbnail sized images.
        self.photoList = pixInfo.get_photoList()
        # img name list
        self.imgNameList = pixInfo.get_imgNameList()
        # img index list for select preview
        self.indexList = pixInfo.get_indexList()
        # feature Matrix
        self.featureM = pixInfo.get_featureM()
        # relevance list
        self.relevanceList = pixInfo.get_relevanceList()
        # checkboxes list
        self.relBoxBools = [tk.IntVar() for i in range(len(self.imageList))]
        # Image size for formatting.
        self.xmax = pixInfo.get_xmax()
        self.ymax = pixInfo.get_ymax()
        # predefined column number for result listframe below
        self.colnum = 10
        # image name
        self.imageName=""
        # image index
        self.index = 0
        # Define window size
        master.geometry("1250x750")

        listFrame = tk.Frame(master, relief="groove", borderwidth=1, padx=5, pady=5)
        listFrame.grid(row=1, column=0, columnspan=4, sticky="news", padx=10, pady=5)

        self.listframe = listFrame  # Save the reference to self.listframe

        # Create Control frame.
        controlFrame = tk.Frame(master, width=300)
        controlFrame.grid(row=0, column=3, sticky="sen", padx=10, pady=5)

        # Create listbox frame
        previewListFrame = tk.Frame(master, width=30, height=self.ymax+100, borderwidth=1)
        previewListFrame.grid_propagate(0)
        previewListFrame.grid(row=0, column=0, sticky="news", padx=5, pady=5)

         # Create Preview frame.
        previewFrame = tk.Frame(master, width=self.xmax+245, height=self.ymax+150, borderwidth=5,
                             relief="groove", highlightbackground='RED')
        previewFrame.grid_propagate(0)
        previewFrame.grid(row=0, column=1, sticky="news", padx=(5, 0), pady=5)
        self.previewFrame = previewFrame

        # Initialize selectImg attribute
        self.selectImg = tk.Label(self.previewFrame)
        self.selectImg.grid(row=0, column=0, sticky="news")

        # Create Results frame.
        master.rowconfigure(0, weight=0)
        master.columnconfigure(0, weight=1)
        master.rowconfigure(1, weight=1)
        master.columnconfigure(1, weight=1)
        master.columnconfigure(2, weight=1)
        master.columnconfigure(3, weight=1)
        listFrame.rowconfigure(0, weight=1)
        listFrame.columnconfigure(0, weight=1)
        listFrame.columnconfigure(1, weight=0)
        controlFrame.rowconfigure(0, weight=1)
        controlFrame.columnconfigure(0, weight=1)
        previewFrame.rowconfigure(0, weight=1)
        previewFrame.columnconfigure(0, weight=1)

        # create listbox
        self.listbox = tk.Listbox(self.listframe, selectmode=tk.SINGLE)
        self.listbox.grid(row=0, column=0, sticky='news')
        self.listbox.bind('<<ListboxSelect>>', self.update_preview)

        self.plist = tk.Listbox(previewListFrame, selectmode="browse", height=14)
        for i in range(len(self.imageList)):
            self.plist.insert(i, self.getFilename(self.imageList[i].filename))
        self.plist.activate(1)
        self.plist.bind('<<ListboxSelect>>', self.update_preview)

        # create list
        self.listbox = tk.Frame(listFrame)
        self.listbox.rowconfigure(0, weight=1)
        self.listbox.columnconfigure(0, weight=1)
        self.listbox.grid_propagate(False)

        # add a canvas inside list
        self.listcanvas = tk.Canvas(self.listbox)
        self.listcanvas.grid(row=0, column=0, sticky="news")

        # add another frame for gridview images
        self.gridframe = tk.Frame(self.listcanvas)
        self.listcanvas.create_window((0, 0), window=self.gridframe, anchor='nw')
        
        # get a grid view of clicable images
        listsize = len(self.photoList)

        # 8 images per row, then
        rownum = int(math.ceil(listsize/float(self.colnum)))
        fullsize = (0, 0, (self.xmax*self.colnum), (self.ymax*rownum))
        for i in range(rownum):
            for j in range(self.colnum):
                if (i*self.colnum+j) < listsize:
                    pho = self.photoList[i*self.colnum+j]
                    index = i * self.colnum + j  # Calculate the index
                    pImg = tk.Button(self.gridframe, image=pho, fg='white', relief='flat', bg='white', bd=0, justify='center')
                    pImg.configure(image=pho)
                    pImg.photo = pho
                    pImg.config(command=lambda idx=index: self.display_image(self.imgNameList[idx], idx))
                    pImg.grid(row=i, column=j, sticky='news', padx=5, pady=5)

        self.gridframe.update_idletasks()
        self.listcanvas.config(scrollregion=fullsize)
        self.listbox.grid(row=0, column=0, sticky='news')
        self.origY = self.listcanvas.yview()[0]
        self.listbox.bind('<<CanvasSelect>>', self.update_preview)

        # update listbox
        self.plist.delete(0, 'end')
        for i in range(len(self.imageList)):
            self.plist.insert(i, self.getFilename(self.imageList[i].filename))

        # Color-code button
        self.b1 = tk.Button(controlFrame, text="Sort by Color-Code", padx=5, width=15, command=lambda: self.find_distance(method='CC'))
        self.b1.grid(row=1, column=1, sticky="news",padx=5, pady=2)

        # Intensity Button
        b2 = tk.Button(controlFrame, text="Sort by Intensity", padx=5, width=15, command=lambda: self.find_distance(method='inten'))
        b2.grid(row=1, column=0, sticky="news",padx=5, pady=2)

        # Color-code+intensity Button
        colorPlusInten = tk.Button(controlFrame, text="Sort by Color-code + Intensity", padx=5, width=15, wraplength=100, command=lambda: self.find_distance(method='CC+inten'))
        colorPlusInten.grid(row=2, column=0, sticky='news',padx=5, pady=2)

        scrollbar_x = Scrollbar(self.listframe, orient="horizontal")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        # Create canvas for thumbnails
        self.listcanvas = tk.Canvas(self.listbox, xscrollcommand=scrollbar_x.set)
        self.listcanvas.grid(row=0, column=0, sticky="news")
        scrollbar_x.config(command=self.listcanvas.xview)

        # checkbox for RF
        self.rfbool = tk.IntVar()
        self.rfbox = tk.Checkbutton(controlFrame, text='Enable Relevance Feedback', padx=5, width=15, wraplength=100, variable=self.rfbool, offvalue=0, onvalue=1, command=lambda: self.add_checkbox(scrollbar_x))
        self.rfbox.grid(row=2, column=1, sticky='news', padx=5, pady=2)

        # Reset Button
        resetButton = tk.Button(controlFrame, text='Reset', padx=5, width=15, command=lambda : self.reset())
        resetButton.grid(row=3, column=0, sticky="news",padx=5, pady=2)
        
        # Quit Button
        quitButton = tk.Button(controlFrame, text='Quit', padx=5, width=15, command=lambda: sys.exit(0))
        quitButton.grid(row=3, column=1, sticky="news",padx=5, pady=2)

        # Create a Label for displaying the page number
        self.page_label = tk.Label(master, text="Page: 1", font=("Arial", 10))
        self.page_label.grid(row=2, column=1, sticky="news", padx=5, pady=5)


        # resize option for control frame
        controlFrame.rowconfigure(0, weight=1)
        controlFrame.rowconfigure(1, weight=1)
        controlFrame.rowconfigure(2, weight=1)
        controlFrame.rowconfigure(3, weight=1)

        # Layout Preview (The two big frames on top middle ).
        # preview the first image
        image = self.imageList[0]
        self.previewFrame.update()
        # resize to fit the frame
        imResize = image.resize(self.resize_img(self.previewFrame.winfo_width(), self.previewFrame.winfo_height(), image), ANTIALIAS)
        pho = ImageTk.PhotoImage(imResize)
        self.previewImg = tk.Label(self.previewFrame, image=pho)
        self.previewImg.photo = pho
        self.previewImg.grid(row=0, column=0, sticky='news')

        self.page_size = 20  # Set the page size to 20
        self.current_page = 0
        self.next_button = tk.Button(controlFrame, text="Next", padx=5, width=15, command=self.next_page)
        self.next_button.grid(row=4, column=1, sticky="news", padx=5, pady=2)

        self.prev_button = tk.Button(controlFrame, text="Prev", padx=5, width=15, command=self.prev_page)
        self.prev_button.grid(row=4, column=0, sticky="news", padx=5, pady=2)

        # Initialize the thumbnails grid.
        self.update_thumbnail_grid()

    # Update the thumbnail image grid
    def update_thumbnail_grid(self):
        start_index = (self.current_page)* self.page_size
        end_index = min(start_index + self.page_size, len(self.imageList))
        self.update_listbox(start_index, end_index)

        self.gridframe.update_idletasks()
        self.listcanvas.config(scrollregion=self.listcanvas.bbox("all"))

        current_page_number = self.current_page + 1  # 0-based index to 1-based page number
        total_pages = math.ceil(len(self.imageList) / self.page_size)
        self.page_label.config(text=f"Page: {current_page_number}/{total_pages}")

        # Enable both buttons initially
        self.prev_button['state'] = 'normal'
        self.next_button['state'] = 'normal'

        # Disable the "Prev" button on the first page
        if self.current_page == 0:
            self.prev_button['state'] = 'disabled'

        # Disable the "Next" button on the last page
        if (self.current_page + 1) * self.page_size >= len(self.imageList):
            self.next_button['state'] = 'disabled'

    # Display images in grid w and w/o sorting
    def update_listbox(self, start_index, end_index):
        # Update the listbox with thumbnails.
        self.plist.delete(0, 'end')
        for i in range(start_index, end_index):
            img_index = self.indexList[i]
            img_name = self.getFilename(self.imageList[img_index].filename)
            self.plist.insert(i, img_name)

        # Destroy the existing grid frame.
        self.gridframe.destroy()
        self.gridframe = tk.Frame(self.listcanvas)
        self.gridframe.update_idletasks()
        self.listcanvas.create_window(
            (0, 0), window=self.gridframe, anchor='nw')

        # Populate the grid with thumbnails and names.
        listsize = len(self.photoList)
        rownum = int(math.ceil(listsize / float(self.colnum)))
        fullsize = (0, 0, (self.xmax * self.colnum), (self.ymax * rownum))
        for i in range(start_index // self.colnum, (end_index + self.colnum - 1) // self.colnum):
            for j in range(self.colnum):
                index = i * self.colnum + j
                if start_index <= index < end_index <= listsize:
                    pframe = tk.Frame(self.gridframe, padx=5, pady=5)  # Add padding to the frame
                    pframe.grid(row=i, column=j, sticky="news", padx=5, pady=5)

                    pho = self.photoList[self.indexList[index]]
                    pImg = tk.Button(pframe, image=pho, fg='white',
                                    relief='flat', bg='white', bd=0, justify='center', padx=5, pady=5)  # Adjust padx and pady
                    pImg.configure(image=pho)
                    pImg.photo = pho
                    pImg.config(
                        command=lambda idx=index: self.display_image(self.imgNameList[self.indexList[idx]], self.indexList[idx]))
                    pImg.grid(row=0, column=0, sticky='news')

                    # Add label to display image name below the thumbnail.
                    img_name = self.getFilename(self.imageList[self.indexList[index]].filename)[7:]
                    label = tk.Label(pframe, text=img_name, font=("Arial", 8), wraplength=100)
                    label.grid(row=1, column=0, sticky='news')

                    if self.rfbool.get() == 1:
                        # add checkbox
                        pcheckbox = tk.Checkbutton(pframe, text='Relevant',
                                                variable=self.relBoxBools[self.indexList[index]],
                                                command=lambda x=self.indexList[index]: self.updateWeight(x))
                        if self.relevanceList[self.indexList[index]] == 1:
                            pcheckbox.select()
                        pcheckbox.grid(row=2, column=0, sticky='news')

        # Adjust size of canvas.
        self.gridframe.update_idletasks()
        self.listcanvas.config(scrollregion=fullsize)

    # Function for implementing next page pagination logic
    def next_page(self):
        if (self.current_page + 1) * self.page_size < len(self.imageList):
            self.current_page += 1
            self.update_thumbnail_grid()
        else:
            # Disable the "Next" button on the last page
            self.next_button['state'] = 'disabled'

    # Function for implementing previous page pagination logic
    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_thumbnail_grid()
        else:
            # Disable the "Prev" button on the first page
            self.prev_button['state'] = 'disabled'
        
    # Resize and scale the image
    def resize_img(self, rwidth, rheight, img):
        oldwidth = img.size[0]
        oldheight = img.size[1]
        ratio = float(oldwidth)/oldheight
        if ratio >= 1:
            return (int(rwidth), int(rwidth/ratio))
        else:
            return (int(rheight*ratio), int(rheight))

    # Update the query image preview
    def update_preview(self, event):
        selected_indices = self.plist.curselection()
        if selected_indices:
            selected_index = selected_indices[0]
            # Get the corresponding image index in imgNameList
            img_index = self.indexList[selected_index]
        try:
            self.previewI = self.plist.curselection()[0]
        except:
            self.previewI = 0
        image = self.imageList[int(self.previewI)]
        # resize to fit the frame
        self.previewFrame.update()
        imResize = image.resize(self.resize_img(self.previewFrame.winfo_width(
        )-10, self.previewFrame.winfo_height()-10, image), ANTIALIAS)
        pho = ImageTk.PhotoImage(imResize)
        self.previewImg.configure(
            image=pho)
        self.previewImg.photo = pho

    # Get the image distance using Manhattan distance function
    def find_distance(self, method):

        i = self.index  # get the current index

        # display error message box if no image selected but clicked on Sort by CC + Intensity
        if self.rfbool.get() == 1 and all(var.get() == 0 for var in self.relBoxBools):
            messagebox.showinfo("Error", "Please Select Relevant Images")
            return
        
        pixList = list(self.imageList[i].getdata())
        targetCC, targetIntens = self.pixInfo.encode(pixList)
        targetpixSize = len(pixList)

        # if user selects Intensity 
        if (method == 'inten'):
            MDs = self.calc_manhattan_distance(targetIntens, self.intenCode,
                              targetpixSize, self.pixInfo.get_pixSizeList())
        
        # if user selects Color Code
        elif (method=='CC'):
            MDs = self.calc_manhattan_distance(targetCC, self.colorCode,
                              targetpixSize, self.pixInfo.get_pixSizeList())
            
        # if user selects Color Code + Intensity
        elif (method=='CC+inten'):
            targetFM = self.featureM[i]
    
            # check if RF is checked
            if (self.rfbool.get() == 0):
                # no need to do gaussian
                MDs=self.calc_weighted_distance(targetFM, self.featureM, np.ones(targetFM.shape[0])*1/targetFM.shape[0])
            else:
                # get the relevant images rows
                relevantM = []
                for i in range(len(self.relevanceList)):
                    if self.relevanceList[i]==1:
                        relevantM.append(self.featureM[i])

                # display error message box if no image selected but clicked on Sort by CC + Intensity
                if not relevantM:
                    messagebox.showinfo("Error", "Please Select Relevant Images")
                    return
                
                # calculate weight
                stdM = []
                for i in range(len(relevantM[0])):
                    standarddev = stdev(np.array(relevantM)[:,i])
                    stdM.append(standarddev)
                stdM = np.array(stdM)
                weightM = []
                for i in range(len(stdM)):
                    if stdM[i]==0:
                        # check average
                        avg = (np.array(relevantM)[:,i]).mean()
                        if avg !=0:
                            weight = 1/(0.5*min(stdM[stdM!=0]))
                        else:
                            weight = 0
                    else:
                        weight = 1/stdM[i]
                    weightM.append(weight)
                weightM = np.array(weightM)
                weightM = weightM/np.linalg.norm(weightM, ord=1)
                MDs = self.calc_weighted_distance(targetFM, self.featureM, weightM)

        MDTuples = [(self.photoList[i], MDs[i])
                    for i in range(len(self.imageList))]
        MDTuplesNames = {self.imgNameList[i]: MDs[i]
                         for i in range(len(self.imageList))}
        self.update_results(MDTuples, MDTuplesNames)
        self.update_thumbnail_grid()
        return

    # Calculates the Manhattan distance
    def calc_manhattan_distance(self, targetIntens, intenCodes, targetpixSize, pixSizeList):
        ret = []
        for j in range(len(intenCodes)):
            code = intenCodes[j]
            sum = 0
            for i in range(len(targetIntens)):
                sum += math.fabs(targetIntens[i]/float(targetpixSize) -
                                 float(code[i])/pixSizeList[j])
            ret.append(sum)
        return ret

    # Get the weighted distance for each of the images
    def calc_weighted_distance(self, targetFM, featureM, weightM):
        ret=[]
        for i in range(featureM.shape[0]):
            sum = 0
            for j in range(featureM.shape[1]):
                weight = weightM[j]
                sum += weight* math.fabs(featureM[i][j]-targetFM[j])
            ret.append(sum)
        return ret

    # Update the results window with the sorted results
    def update_results(self, sortedTup, MDTuplesImg):
        # sort Manhattan Distance Arrays
        sorttuples = sorted(sortedTup, key=lambda x: x[1])
        self.indexList = sorted(self.indexList, key=lambda i: sortedTup[i][1])
        photoRemain = [(self.pixInfo.imgNameList[i], sorttuples[i][0])
                       for i in range(len(sorttuples))]
        self.gridframe.destroy()
        self.gridframe = tk.Frame(self.listcanvas)
        self.gridframe.update_idletasks()
        self.listcanvas.create_window(
            (0, 0), window=self.gridframe, anchor='nw')
        # get a grid view of images
        listsize = len(self.photoList)
        # 8 images per row, then
        rownum = int(math.ceil(listsize/float(self.colnum)))
        fullsize = (0, 0, (self.xmax*self.colnum), (self.ymax*rownum))
        for i in range(rownum):
            for j in range(self.colnum):
                if (i*self.colnum+j) < listsize:
                    pframe = tk.Frame(self.gridframe)
                    pframe.grid(row=i, column=j, sticky="news", padx=5, pady=5)
                    pho = photoRemain[i*self.colnum+j][1]
                    pImg = tk.Button(pframe, image=pho, fg='white',
                                  relief='flat', bg='white', bd=0, justify='center')
                    pImg.configure(image=pho)
                    pImg.photo = pho
                    pImg.config(command=lambda i=i, j=j: self.display_image(self.imgNameList[self.indexList[i*self.colnum+j]], self.indexList[i*self.colnum+j]))

                    pImg.grid(row=0, column=0, sticky='news')
                    if (self.rfbool.get() ==1):
                        # add checkbox
                        pcheckbox = tk.Checkbutton(pframe, text='Relevant', 
                            variable=self.relBoxBools[self.indexList[i*self.colnum+j]],
                            command=lambda x=self.indexList[i*self.colnum+j]: self.updateWeight(x))
                        if self.relevanceList[self.indexList[i*self.colnum+j]]==1:
                            pcheckbox.select()
                        pcheckbox.grid(row=1, column=0, sticky='news')
        # adjust size of canvas
        self.gridframe.update_idletasks()
        self.listcanvas.config(scrollregion=fullsize)
        self.listcanvas.yview_moveto(self.origY)
        self.current_page = 0

    # Display the image with filename
    def display_image(self, filename, index):
        image = Image.open(filename)
        self.imageName=filename
        self.index = index

        # resize to fit the frame
        self.previewFrame.update()
        imResize = image.resize((400, 200), ANTIALIAS)
        pho = ImageTk.PhotoImage(imResize)
        self.previewImg.configure(
            image=pho)
        self.previewImg.photo = pho

    # Add checkbox for the selectPreview pictures
    def add_checkbox(self,scrollbar_x):

        # destroy grid inside canvas
        self.gridframe.destroy()
        # recreate
        self.gridframe = tk.Frame(self.listcanvas)
        self.gridframe.update_idletasks()
        self.listcanvas.create_window((0, 0), window=self.gridframe, anchor='nw')

        # get a grid view of images
        listsize = len(self.photoList)
        items_per_page = 20
        self.current_page = 1
        start_index = (self.current_page - 1) * items_per_page
        end_index = min(self.current_page * items_per_page, listsize)
        rownum = int(math.ceil((end_index - start_index) / float(self.colnum)))
        fullsize = (0, 0, (self.xmax * self.colnum), (self.ymax * rownum))

        for i in range(rownum):
            for j in range(self.colnum):
                index = start_index + i * self.colnum + j
                if index < end_index:
                    pframe = tk.Frame(self.gridframe)
                    pframe.grid(row=i, column=j, sticky="news", padx=5, pady=5)
                    pho = self.photoList[self.indexList[index]]
                    pImg = tk.Button(pframe, image=pho, fg='white', relief='flat', bg='white', bd=0, justify='center')
                    pImg.configure(image=pho)
                    pImg.photo = pho
                    pImg.config(command=lambda idx=index: self.display_image(self.imgNameList[self.indexList[idx]], self.indexList[idx]))
                    pImg.grid(row=0, column=0, sticky='news')

                    # Add label to display image name below the thumbnail.
                    img_name = self.getFilename(self.imageList[self.indexList[index]].filename)[7:]
                    label = tk.Label(pframe, text=img_name, font=("Arial", 8), wraplength=100)
                    label.grid(row=1, column=0, sticky='news')
                    
                    # Get relevant images
                    if self.rfbool.get() == 1:
                        pcheckbox = tk.Checkbutton(pframe, text='Relevant',
                                                variable=self.relBoxBools[self.indexList[index]],
                                                command=lambda x=self.indexList[index]: self.updateWeight(x))
                        pcheckbox.grid(row=2, column=0, sticky='news')

        # Add horizontal scrollbar to canvas
        scrollbar_x.config(command=self.listcanvas.xview)
        self.listcanvas.config(xscrollcommand=scrollbar_x.set)
        self.gridframe.update_idletasks()
        self.listcanvas.config(scrollregion=self.listcanvas.bbox("all"))

    # Update weight after each iteration
    def updateWeight(self, index):
        relBool = self.relBoxBools[index]
        self.relevanceList[index] = relBool.get()

    # Get filename from filepath
    def getFilename(self, fn):
        i = fn.rfind('/')
        return fn[i+1:]
    
    # Reset the application
    def reset(self):
        self.previewI = 0  #Reset the preview image index to 0
        self.index = 0  #Reset the image index to 0
        self.current_page = 0  # Reset the current page to the first page
        self.page_size = 20  # Set the page size to 20
        self.indexList = list(range(len(self.imageList)))
        self.relevanceList = [0] * len(self.imageList)
        self.relBoxBools = [tk.IntVar() for _ in range(len(self.imageList))]
        self.rfbox.deselect()

        # Destroy the existing grid frame.
        self.gridframe.destroy()
        self.gridframe = tk.Frame(self.listcanvas)
        self.gridframe.update_idletasks()
        self.listcanvas.create_window((0, 0), window=self.gridframe, anchor='nw')

        # Get a grid view of images for the current page.
        self.update_thumbnail_grid()
        self.update_preview(0)

# Executable section.
if __name__ == '__main__':

    root = tk.Tk()
    root.title('CBIR With Relevance Feedback')
    root.state('zoomed')
    pixInfo = PixInfo(root)
    imageViewer = ImageViewer(root, pixInfo)
    root.mainloop()
