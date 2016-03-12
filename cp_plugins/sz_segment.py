'''<b>sz_segment</b> - performing secondary refinery for cytoplasm segmentation using both cytoplasm mask from NC_Cyto_Segment module and original gray cytoplasm channel

<hr>
<p>
The segmentation uses cytoplasm mask from NC_Cyto_Segment module. It is recommend to use a large dilation (10~20pixels) for NC_Cyto_Segment.
The module further capture local information from the cytoplasm mask by performing a secondary clustering. 

</p>


'''

import os
import sys

import cellprofiler.settings as cps
import cellprofiler.cpimage as cpi
import cellprofiler.cpmodule as cpm

import imagej.imageprocessor as ijiproc


class sz_segment(cpm.CPModule):
    module_name = "sz_segment"
    category = "DImage"
    variable_revision_number = 1
        
    def create_settings(self):
        self.input_cyto_mask_image_name = cps.ImageNameSubscriber("dilated cyto mask image:",
                                                                doc = """
                                                                cytoplasm mask image,
                                                                white for foreground pixels,
                                                                black for background pixels
                                                                """)
        
        self.input_cyto_gray_image_name = cps.ImageNameSubscriber("cytoplasm gray image",
                                                                  doc = """
                                                                  cytoplasm gray-value image, preferable 8-bit
                                                                  """)
        
        self.output_image_name = cps.ImageNameProvider("output image:","OutputImage", 
                                                       doc = """
                                                       binary mask of cytoplasm,
                                                       white for foreground pixels,
                                                       black for background pixels
                                                       """)
        
        self.input_gaussian_filter = cps.Float("Gaussian filter size",value=3,
                                               doc = """
                                               Gaussian filter size for noise suppression in cytoplasm channel,
                                               recommended around 6~8, suppressing pixel noises or texture                                               
                                               """)
        
        self.input_rolling_ball = cps.Float("rolling ball size",value=256,
                                            doc = """
                                            rolling ball kernel size, recommended around 1/4 of image dimensionality, remove uneven illumination
                                            """)
        
        self.input_low_seed = cps.Float("low seed",value=10,
                                        doc = """
                                        initial intensity value for background
                                        """)
        
        self.input_high_seed = cps.Float("high seed",value=50,
                                         doc = """
                                         initial intensity value for foreground
                                         """)
        
    def settings(self):
        return [self.input_cyto_mask_image_name,
                self.input_cyto_gray_image_name, 
                self.output_image_name, 
                self.input_gaussian_filter,
                self.input_rolling_ball,
                self.input_low_seed,
                self.input_high_seed]
    

    def visible_settings(self):
        result = [self.input_cyto_mask_image_name,
                  self.input_cyto_gray_image_name, 
                  self.output_image_name,
                  self.input_gaussian_filter,
                  self.input_rolling_ball,
                  self.input_low_seed,
                  self.input_high_seed]
        return result

    def run(self, workspace):
        import cellprofiler.utilities.jutil as jb
        jb.attach()#initialize JVM
        
        cyto_mask_image_name = self.input_cyto_mask_image_name.value
        cyto_gray_image_name = self.input_cyto_gray_image_name.value        
        output_image_name = self.output_image_name.value
        workspace.gsize = self.input_gaussian_filter.value
        workspace.rsize = self.input_rolling_ball.value
        workspace.lowseed = self.input_low_seed.value
        workspace.highseed = self.input_high_seed.value
        
        image_set = workspace.image_set
        
        #prepare input image        
        input_image_cyto_mask = image_set.get_image(cyto_mask_image_name, must_be_grayscale = True)
        input_image_cyto_gray = image_set.get_image(cyto_gray_image_name, must_be_grayscale = True)
        
        input_pixels_cyto_mask = input_image_cyto_mask.pixel_data
        input_pixels_cyto_gray = input_image_cyto_gray.pixel_data
        
        ij_processor_cyto_mask = ijiproc.make_image_processor((input_pixels_cyto_mask*255.0).astype('float32'))
        ij_processor_cyto_gray = ijiproc.make_image_processor((input_pixels_cyto_gray*255.0).astype('float32'))
        #JavaScript API
        script = """
        var cytomask = Packages.ij.ImagePlus("cyto_mask",ij_processor_cyto_mask);
        var cytogray = Packages.ij.ImagePlus("cyto_gray",ij_processor_cyto_gray);
        
        Packages.ij.IJ.run(cytomask, "8-bit", "");
        Packages.ij.IJ.run(cytogray, "8-bit", "");
        
        cytomaskIP=cytomask.getProcessor();
        cytograyIP=cytogray.getProcessor();
        
        masker=new Packages.DImage.Masking.SZ_Segment();
        
        masker.equalize=true;
        masker.gsize=gsize;
        masker.rsize=rsize;
        masker.lseed=lowseed;
        masker.hseed=highseed;
        masker.lowbound=0.6;
        masker.highbound=0.8;
        masker.minstd=5;
        
        output_proc=masker.segment(cytograyIP, cytomaskIP);
        
        """
        #img.show();
        #Packages.ij.WindowManager.setCurrentWindow(img.getWindow());
        #"""
        in_params={
                   "name":output_image_name,
                   "ij_processor_cyto_mask": ij_processor_cyto_mask,
                   "ij_processor_cyto_gray": ij_processor_cyto_gray,
                   "gsize":workspace.gsize,
                   "rsize":workspace.rsize,
                   "lowseed":workspace.lowseed,
                   "highseed":workspace.highseed}
        out_params={"output_proc":None}
        jb.run_script(script, bindings_in = in_params,bindings_out = out_params)
        #prepare output image
        output_pixels = ijiproc.get_image(out_params["output_proc"], False)
        output_image = cpi.Image(output_pixels, parent_image = input_image_cyto_gray)
        
        #write output
        image_set.add(output_image_name, output_image)
        
        workspace.intput_pixels_cyto_gray = input_pixels_cyto_gray
        workspace.output_pixels = output_pixels


    def is_interactive(self):
        return False
    
    def display(self, workspace, figure):
        #prepare plot area
        figure.set_subplots((2,1))
        
        figure.subplot_imshow_grayscale(0, 0, workspace.intput_pixels_cyto_gray, title = self.input_cyto_gray_image_name.value)
        
        #display binary mask
        figure.subplot_imshow_grayscale(1, 0, workspace.output_pixels, title = self.output_image_name.value)
