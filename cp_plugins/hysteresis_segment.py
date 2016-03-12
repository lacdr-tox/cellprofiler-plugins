'''<b>Hysteresis_Segment</b> - perform Hysteresis thresholding segmentation algorithm from ImageJ in a seamless mode

<hr>
<p>
Hysteresis thresholding algorithm is an image segmentation algorithm based on edge reconstruction. 
It divides all pixels into strong edges and weak edges using two different threshold level.
By attaching weak edges to strong edge, the segmentation completes the edge of objects.
</p>

'''

import os
import sys

import cellprofiler.settings as cps
import cellprofiler.cpimage as cpi
import cellprofiler.cpmodule as cpm

import imagej.imageprocessor as ijiproc


class Hysteresis_Segment(cpm.CPModule):
    module_name = "Hysteresis_Segment"
    category = "DImage"
    variable_revision_number = 1
        
    def create_settings(self):
        self.input_image_name = cps.ImageNameSubscriber("input image name:",
                                                        doc = """
                                                        Gray-value image only, no color image is allowed, 
                                                        preferable with an original dynamic range of 8-bit or 16-bit.
                                                        There is no need to reverse intensity if ImageJ is set correctly.
                                                        """)
        
        self.output_image_name = cps.ImageNameProvider("output image name:","OutputImage", 
                                                       doc = """
                                                       binary mask output, returns a 8-bit two color image, 
                                                       white pixels belong to foreground, 
                                                       black pixels belong to background.
                                                       """)
        
        self.input_gaussian_filter = cps.Float("Gaussian Filter Size",value=2,
                                               doc="""
                                               Gaussian filter size, recommended around 1~4, 
                                               suppressing pixel noises or intensity variations.
                                               If other blurring algorithm has been employed already, 
                                               this value can be set to 0 to disable the Gaussian filter.
                                               """)
        
        self.input_rolling_ball = cps.Float("rolling ball size:",value=256,
                                            doc="""
                                            rolling ball kernel size, recommended around 1/4 of image dimensionality.
                                            It removes uneven illumination by estimating the background using either a spherical or parabolic kernel. 
                                            By default, the rolling ball uses spherical kernel.
                                            The spherical kernel is evenly weighted. Ideal for objects sharing similar morphology
                                            The parabolic kernel is more strong at the center while weaker at both tail. Ideal for objects do not share similar morphology.
                                            It can also be used to extract foci or speckle from cell background by considering cell background as part of background.
                                            """)
                
        self.input_low_seed = cps.Float("low seed:",value=10,
                                        doc="""
                                        initial intensity value for background
                                        """)
        
        self.input_high_seed = cps.Float("high seed:",value=50,
                                         doc="""
                                         initial intensity value for foreground
                                         """)
        
    def settings(self):
        return [self.input_image_name, 
                self.output_image_name, 
                self.input_gaussian_filter,
                self.input_rolling_ball,
                self.input_low_seed,
                self.input_high_seed]
    

    def visible_settings(self):
        result = [self.input_image_name,
                  self.output_image_name,
                  self.input_gaussian_filter,
                  self.input_rolling_ball,
                  self.input_low_seed,
                  self.input_high_seed]
        return result

    def run(self, workspace):
        import cellprofiler.utilities.jutil as jb
        
        jb.attach()#initialize JVM
        
        input_image_name = self.input_image_name.value
        output_image_name = self.output_image_name.value
        self.gsize = self.input_gaussian_filter.value
        self.rsize = self.input_rolling_ball.value
        self.lowseed = self.input_low_seed.value
        self.highseed = self.input_high_seed.value
        
        image_set = workspace.image_set
        
        #prepare input image        
        input_image = image_set.get_image(input_image_name, must_be_grayscale = True)        
        input_pixels = input_image.pixel_data
        ij_processor = ijiproc.make_image_processor((input_pixels*255.0).astype('float32'))
        #JavaScript API
        script = """       
        var img=Packages.ij.ImagePlus(name,ij_processor);
        Packages.ij.IJ.run(img, "8-bit", "");     
	    var macro="g_size="+gsize+" r_size="+rsize+" low_edge="+lowseed+" high_edge="+highseed+" noise=-1";
        java.lang.System.out.println(macro);        
        Packages.ij.IJ.run(img, "Hysteresis Segment", macro);
        var output_proc=img.getProcessor();
        """
        #img.show();
        #Packages.ij.WindowManager.setCurrentWindow(img.getWindow());
        #"""
        in_params={
                   "name":output_image_name,
                   "ij_processor": ij_processor,
                   "gsize":self.gsize,
                   "rsize":self.rsize,
                   "lowseed":self.lowseed,
                   "highseed":self.highseed}
        out_params={"output_proc":None}
        r = jb.run_script(script, bindings_in = in_params,bindings_out = out_params)
        
        #prepare output image
        output_pixels = ijiproc.get_image(out_params["output_proc"], False)
        output_image = cpi.Image(output_pixels, parent_image = input_image)
        
        #write output
        image_set.add(output_image_name, output_image)
        
        
	workspace.input_pixels = input_pixels
        workspace.output_pixels = output_pixels
        

    def is_interactive(self):
        return False
    
    def display(self, workspace, figure):
        #prepare plot area
        figure.set_subplots((2,1))
        
        #display original image
        figure.subplot_imshow_grayscale(0, 0, workspace.input_pixels, title = self.input_image_name.value)
        
        #display binary mask
        figure.subplot_imshow_grayscale(1, 0, workspace.output_pixels, title = self.output_image_name.value)

