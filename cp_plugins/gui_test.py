'''<b>GUI_Test</b> - an example image processing module
'''
import cellprofiler.cpimage as cpi
import cellprofiler.cpmodule as cpm
import cellprofiler.settings as cps

import imagej.imageprocessor as ijiproc
import hashlib
class GUI_Test(cpm.CPModule):
   
    module_name = "GUI_Test"
    category = "DImage"
    variable_revision_number = 1
       
    def create_settings(self):
        
        self.config_usr = cps.Text("config_usr", "")
        self.config_pwd = cps.Text("config_pwd", "")
        self.project_choice = cps.Choice("Project:", [""] , doc = "choose project")        
        self.exp_choice = cps.Choice("Exp:", [""], doc = "choose experiment")
        self.plate_choice = cps.Choice("Plate:", [""], doc = "choose plate")
        self.well_choice = cps.Choice("Well:", [""], doc = "choose well")
        self.site_choice = cps.Choice("Site:", [""], doc = "choose site")
        self.refresh_button = cps.DoSomething("Refresh filter","Refresh", self.refresh_filter)
        self.add_image_button = cps.DoSomething("Confirm selection","Confirm", self.confirm_image)
        self.cache_loc = cps.DirectoryPath("cache location")
        
        self.pathnames = []
        self.pathname_count = cps.HiddenCount(self.pathnames)
        
    
    def settings(self):
        result=[self.pathname_count]
        result+=[self.config_usr,self.config_pwd]
        result+=[group.image_name for group in self.pathnames]
        result+=[self.project_choice, self.exp_choice, self.plate_choice,self.well_choice,self.site_choice]
        result+=[self.cache_loc]        
        for group in self.pathnames:
            result+=[group.image_name]     
        return result
    
    def visible_settings(self):
        result=[self.config_usr,self.config_pwd]
        result+=[self.project_choice, self.exp_choice, self.plate_choice,self.well_choice,self.site_choice]
        result+=[self.refresh_button,self.add_image_button]
        result+=[self.cache_loc]
        for group in self.pathnames:
            result+=[group.image_name]     
        return result
    
    def prepare_settings(self, setting_values):
        npaths = int(setting_values[0])#get path count from hidden counter, the zero indicate the index of hidden counter in all setting, see setting(self)
        #print npaths
        del self.pathnames[0:]
        for _ in range(0, npaths):
            self.confirm_image()
    
    def confirm_image(self):
        nrchannel=2;
        del self.pathnames[0:]
        group = cps.SettingsGroup()
        for xx in range(0, nrchannel):
            group.append("image_name", cps.ImageNameProvider("image name", "ch_"+str(xx+1)))
        self.pathnames.append(group)
    
    def add_image(self, can_remove=True):
        group = cps.SettingsGroup()
        group.append("image_name",cps.ImageNameProvider("image name", "ch"+str(len(self.pathnames)+1)))
        group.can_remove = can_remove
        if can_remove:
            group.append("remover", cps.RemoveSettingButton("Remove this path", "Remove", self.pathnames, group))
        self.pathnames.append(group)
        print self.pathname_count,len(self.pathnames)
        
    def refresh_filter(self):
        str_usr=self.config_usr.value;
        str_pwd=self.config_pwd.value;
        
        m = hashlib.sha512()
        m.update(str_pwd)
        str_pwd_hash = m.hexdigest()
        
        m.update(str_usr)        
        str_usr_hash = m.hexdigest()        
        
        hashkey="2708e23fe96fa619f361578850c908be800e54737024ed990131b3d8797ef7cfb6a3656e63ed220dfbdb51c4243576fbef8e0f25bcc341cc029fd841642f4791"
        print str_pwd_hash
        print hashkey
        
        if (str_pwd_hash==hashkey):
            print ('hash check ok')
            newfilterlist={"project":self.project_choice.value,
                             "exp":self.exp_choice.value,
                             "plate":self.plate_choice.value,
                             "well":self.well_choice.value,
                             "site":self.site_choice.value};
            if(self.project_choice.value==""):
                print "no project loaded"
                self.project_choice=cps.Choice("Project:",["*"]+["Project 1","Project 2"], doc=self.project_choice.doc)
                self.exp_choice=cps.Choice("Exp:", ["*"], doc = self.exp_choice.doc)
                self.plate_choice=cps.Choice("Plate:", ["*"], doc = self.plate_choice.doc)
                self.well_choice = cps.Choice("Well:", ["*"], doc = self.well_choice.doc)
                self.site_choice = cps.Choice("Site:", ["*"], doc = self.site_choice.doc)  
            else:
                print "project loaded"
                if(newfilterlist["project"]==self.filterlist["project"]):
                    print "project the same"            
                    if(newfilterlist["exp"]==self.filterlist["exp"]):
                        print "exp the same"               
                        if(newfilterlist["plate"]==self.filterlist["plate"]):
                            print "plate the same"                    
                            if(newfilterlist["well"]==self.filterlist["well"]):
                                print "well the same"                                       
                                if(newfilterlist["site"]==self.filterlist["site"]):                            
                                    print "site the same"                            
                                else:
                                    print "site not the same"                                              
                            else:
                                print "well not the same"
                                self.site_choice = cps.Choice("Site:", ["*"]+["site 1","site 2"], doc = self.site_choice.doc)
                        else:
                            print "plate not the same"
                            self.well_choice = cps.Choice("Well:", ["*"]+["well 1", "well 2"], doc = self.well_choice.doc)
                            self.site_choice = cps.Choice("Site:", ["*"], doc = self.site_choice.doc)
                    else:
                        print "exp not the same"
                        self.plate_choice=cps.Choice("Plate:", ["*"]+["plate 1", "plate 2"], doc = self.plate_choice.doc)
                        self.well_choice = cps.Choice("Well:", ["*"], doc = self.well_choice.doc)
                        self.site_choice = cps.Choice("Site:", ["*"], doc = self.site_choice.doc)   
                else:
                    print "project not the same"
                    self.exp_choice=cps.Choice("Exp:", ["*"]+["exp 1", "exp 2"], doc = self.exp_choice.doc)
                    self.plate_choice=cps.Choice("Plate:", ["*"], doc = self.plate_choice.doc)
                    self.well_choice = cps.Choice("Well:", ["*"], doc = self.well_choice.doc)
                    self.site_choice = cps.Choice("Site:", ["*"], doc = self.site_choice.doc)   
                
            self.filterlist={"project":self.project_choice.value,
                             "exp":self.exp_choice.value,
                             "plate":self.plate_choice.value,
                             "well":self.well_choice.value,
                             "site":self.site_choice.value};
        else:
            print ('hash check not ok')

    def run(self, workspace):
        import javabridge.jutil as jb
        jb.attach()#initialize JVM
        image_set = workspace.image_set
        assert isinstance(image_set, cpi.ImageSet)
        #clean up ImageJ
        jb.run_script('Packages.ij.IJ.run("Close All");')
        jb.detach()#close JVM
        del jb

    def is_interactive(self):
        return False
    #
    # display lets you use matplotlib to display your results. 
    #
    def display(self, workspace):
        #prepare plot area
        figure = workspace.create_or_find_figure(subplots=(2,1))
        lead_subplot = figure.subplot(0,0)
        
