'''<b>CLAHE</b> - perform CLAHE
'''
import cellprofiler.cpimage as cpi
import cellprofiler.cpmodule as cpm
import cellprofiler.settings as cps

import imagej.imageprocessor as ijiproc

class CLAHE(cpm.CPModule):
   
    module_name = "CLAHE"
    category = "DImage"
    variable_revision_number = 1
       
    def create_settings(self):        
        self.input_image_name = cps.ImageNameSubscriber("Input image name:",doc = "Gray-value image only, no color image")
        self.output_image_name = cps.ImageNameProvider("Output image name:","OutputImage", doc = "binary mask output")
        self.input_block_size = cps.Float("block size:",value=64, doc="""initial intensity value for foreground""")
        self.input_histogram_bin = cps.Float("number of histogram bin:",value=128, doc="""intensity suppression""")
        self.input_maximum_slope = cps.Float("maximum slope:",value=5, doc="""higher value higher contrast enhancement, lower value lower contrast enhancement""")
        
    def settings(self):
        return [self.input_image_name, self.output_image_name, self.input_block_size, self.input_histogram_bin, self.input_maximum_slope]
    
    def visible_settings(self):
        result =  [self.input_image_name, self.output_image_name, self.input_block_size, self.input_histogram_bin, self.input_maximum_slope]
        return result

    def run(self, workspace):
        import cellprofiler.utilities.jutil as jb
        jb.attach()#initialize JVM

        input_image_name = self.input_image_name.value
        output_image_name = self.output_image_name.value
        block_size = self.input_block_size.value
        histogram_bin = self.input_histogram_bin.value
        maximum_slope = self.input_maximum_slope.value
        
        image_set = workspace.image_set

        #prepare input image        
        input_image = image_set.get_image(input_image_name, must_be_grayscale = True)        
        input_pixels = input_image.pixel_data
        ij_processor = ijiproc.make_image_processor((input_pixels*255.0).astype('float32'))
        
        #JavaScript API
        script = """       
        var img=Packages.ij.ImagePlus(name,ij_processor);
        Packages.ij.IJ.run(img,"CLAHE ", "blocksize="+blocksize+" histogram="+histogrambin+" maximum="+maximumslope);
        var output_proc=img.getProcessor();
        """
        in_params={
                   "name":output_image_name,
                   "ij_processor": ij_processor,
                   "blocksize": block_size,
                   "histogrambin": histogram_bin,
                   "maximumslope": maximum_slope}
        out_params={"output_proc":None}
        jb.run_script(script, bindings_in = in_params,bindings_out = out_params)
        
        #prepare output image
        output_pixels = ijiproc.get_image(out_params["output_proc"], False)
        output_image = cpi.Image(output_pixels, parent_image = input_image)
        
        #write output
        image_set.add(output_image_name, output_image)
        
        workspace.input_pixels = input_pixels
        workspace.output_pixels = output_pixels


    def is_interactive(self):
        return False
    #
    # display lets you use matplotlib to display your results. 
    #
    
    def display(self, workspace, figure):
        #prepare plot area
        figure.set_subplots((2,1))
        
        #display original image
        figure.subplot_imshow_grayscale(0, 0, workspace.input_pixels, title = self.input_image_name.value)
        
        #display binary mask
        figure.subplot_imshow_grayscale(1, 0, workspace.output_pixels, title = self.output_image_name.value) 