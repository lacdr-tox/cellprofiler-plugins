'''<b>NC_Segment_Hi_Res</b> - perform WMC segmentation for image with very large object and complex texture

<hr>
<p>
An extended version to perform WMC segmentation with complex texture.
This algorithm first performs standard WMC segmentation. Then the shattered masks are stitched using binary closing operator. 
Finally, the stitched mask will be cut by binary watershed. 
</p>

See <b>WMC_Segment</b>
'''

import os
import sys

import cellprofiler.settings as cps
import cellprofiler.cpimage as cpi
import cellprofiler.cpmodule as cpm

import imagej.imageprocessor as ijiproc


class NC_Segment_Hi_Res(cpm.CPModule):
    module_name = "NC_Segment_Hi_Res"
    category = "DImage"
    variable_revision_number = 1
        
    def create_settings(self):
        self.input_image_name = cps.ImageNameSubscriber("input image name:",
                                                        doc = """
                                                        Gray-value image only, no color image
                                                        """)
        
        self.output_image_name = cps.ImageNameProvider("output image name:","OutputImage", 
                                                       doc = """
                                                       binary mask output,
                                                       white for foreground,
                                                       black for background
                                                       """)
        
        self.input_gaussian_filter = cps.Float("Gaussian filter size",value=16,
                                               doc = """
                                               Gaussian filter size, recommended around 1~4, 
                                               suppressing pixel noises or intensity variations.
                                               If other blurring algorithm has been employed already, 
                                               this value can be set to 0 to disable the Gaussian filter.
                                               """)
        
        self.input_rolling_ball = cps.Float("rolling ball size",value=512,
                                            doc = """
                                            rolling ball kernel size, recommended around 1/4 of image dimensionality.
                                            It removes uneven illumination by estimating the background using either a spherical or parabolic kernel. 
                                            By default, the rolling ball uses spherical kernel.
                                            The spherical kernel is evenly weighted. Ideal for objects sharing similar morphology
                                            The parabolic kernel is more strong at the center while weaker at both tail. Ideal for objects do not share similar morphology.
                                            """)
        
        self.input_use_paraboloid = cps.Binary("parabolic kernel", value=True, 
                                               doc = """
                                               whether if rolling ball algorithm will use a parabolic kernel
                                               """)
        
        self.input_noise = cps.Float("noise:",value=10,
                                     doc="""
                                     noise-tolerant level, higher value means less cutting, lower value means more cutting
                                     """)
        
        self.input_low_seed = cps.Float("low seed:",value=10,
                                        doc="""
                                        initial intensity value for background
                                        """)
        
        self.input_high_seed = cps.Float("high seed:",value=50,
                                         doc="""
                                         initial intensity value for foreground
                                         """)
        
        self.input_low_bound = cps.Float("low bound:",value=0.6,
                                         doc="""
                                         lowest prior probability of foreground
                                         """)
        self.input_high_bound = cps.Float("high bound:",value=0.8,
                                          doc="""
                                          highest prior probability of foreground
                                          """)
        
        self.input_use_equalize = cps.Binary("use intensity equalize:", value=True, 
                                             doc="""
                                             whether if intensity equalization is used, the intensity equalization perform a deconvolution operation 
                                             """)
        
    def settings(self):
        return [self.input_image_name, 
                self.output_image_name, 
                self.input_gaussian_filter,
                self.input_rolling_ball,
                self.input_use_paraboloid,
                self.input_noise,
                self.input_low_seed,
                self.input_high_seed,
                self.input_low_bound,
                self.input_high_bound,
                self.input_use_equalize]
    

    def visible_settings(self):
        result = [self.input_image_name,
                  self.output_image_name,
                  self.input_gaussian_filter,
                  self.input_rolling_ball,
                  self.input_use_paraboloid,
                  self.input_noise,
                  self.input_low_seed,
                  self.input_high_seed,
                  self.input_low_bound,
                  self.input_high_bound,
                  self.input_use_equalize]
        return result

    def run(self, workspace):
        import javabridge.jutil as jb
        
        jb.attach()#initialize JVM
        
        #get settings and parameters from the GUI components
        input_image_name = self.input_image_name.value
        output_image_name = self.output_image_name.value
        self.gsize = self.input_gaussian_filter.value
        self.rsize = self.input_rolling_ball.value
        self.noise = self.input_noise.value
        self.lowseed = self.input_low_seed.value
        self.highseed = self.input_high_seed.value
        self.lowbound = self.input_low_bound.value
        self.highbound = self.input_high_bound.value
        self.useparabolic = "use_paraboloid" if self.input_use_paraboloid.value else ""
        self.useequalize = "is_equalize" if self.input_use_equalize.value else ""
        
        image_set = workspace.image_set
        
        #prepare input image
        input_image = image_set.get_image(input_image_name, must_be_grayscale = True)        
        input_pixels = input_image.pixel_data
        ij_processor = ijiproc.make_image_processor((input_pixels*255.0).astype('float32'))#make ImageProcessor object
        
        #prepare JavaScript
        script = """       
        var img=Packages.ij.ImagePlus(name,ij_processor);
        Packages.ij.IJ.run(img, "8-bit", "");
        var macro="g_size="+gsize+" r_size="+rsize+" noise="+noise+" low_seed="+lowseed+" high_seed="+highseed+" low_bound="+lowbound+" high_bound="+highbound+" "+useequalize+" "+useparaboloid;
        java.lang.System.out.println(macro);        
        Packages.ij.IJ.run(img, "NC Segment HiRes", macro);
        var output_proc=img.getProcessor();
        """
        #img.show();
        #Packages.ij.WindowManager.setCurrentWindow(img.getWindow());
        #"""
        #prepare JavaScript inputs and outputs
        in_params={
                   "name":output_image_name,
                   "ij_processor": ij_processor,
                   "gsize":self.gsize,
                   "rsize":self.rsize,
                   "noise":self.noise,
                   "lowseed":self.lowseed,
                   "highseed":self.highseed,
                   "lowbound":self.lowbound,
                   "highbound":self.highbound,
                   "useparaboloid":self.useparabolic,
                   "useequalize":self.useequalize}
        out_params={"output_proc":None}
        
        jb.run_script(script, bindings_in = in_params,bindings_out = out_params)#execute the script
        
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
