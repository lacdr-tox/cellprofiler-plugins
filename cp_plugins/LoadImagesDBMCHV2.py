'''LoadImagesDBMCHV2.py - a plugin that loads some files

'''
import os

from bioformats import load_using_bioformats
import cellprofiler.settings as cps
import cellprofiler.cpimage as cpi
import cellprofiler.cpmodule as cpm
import cellprofiler.measurements as cpmeas
from cellprofiler.modules.loadimages import C_FILE_NAME, C_PATH_NAME#constant value for file and path group
import tempfile
import javabridge.jutil as jb#java bridge
import ConfigParser as inicp#ini parser
from suds.client import Client as wsclient#web service client
import hashlib, uuid

C_GROUP_TAG_SITE = "Metadata_Site"
C_GROUP_TAG_WELL = "Metadata_Well"
C_GROUP_TAG_PLATE = "Metadata_Plate"
C_GROUP_TAG_EXP = "Metadata_Experiment"
C_GROUP_TAG_PROJECT = "Metadata_Project"

usr='kyan'
pwd='19821230'
host='babybear'
port=22;
remoteroot="test_seq/";


allpaths=["test_seq001.bmp","test_seq002.bmp","test_seq003.bmp","test_seq004.bmp","test_seq005.bmp","test_seq006.bmp","test_seq007.bmp","test_seq008.bmp","test_seq009.bmp","test_seq010.bmp","test_seq011.bmp","test_seq012.bmp"]
nrimage=len(allpaths)
allsites=["Site_01","Site_01","Site_01","Site_02","Site_02","Site_02","Site_01","Site_01","Site_01","Site_02","Site_02","Site_02"]
allwells=["A01","A01","A01","A01","A01","A01","B01","B01","B01","B01","B01","B01"]
allplates=["Plate_1","Plate_1","Plate_1","Plate_1","Plate_1","Plate_1","Plate_2","Plate_2","Plate_2","Plate_2","Plate_2","Plate_2"]
allexps=["Exp_1","Exp_1","Exp_1","Exp_1","Exp_1","Exp_1","Exp_1","Exp_1","Exp_1","Exp_1","Exp_1","Exp_1"];
allprojects=["Project_1","Project_1","Project_1","Project_1","Project_1","Project_1","Project_1","Project_1","Project_1","Project_2","Project_2","Project_2"];

dbprojectlist=["project1","project2"]
dbexplist=["exp1","exp2"]
dbplatelist=["dum1","dum2"]
class LoadImagesDBMCHV2(cpm.CPModule):
    variable_revision_number=1
    module_name = "LoadImagesDBMCHV2"
    category = "ImageDB"
    
    def create_settings(self):
        
        self.config_usr = cps.Text("config_usr", "")
        self.config_pwd = cps.Text("config_pwd", "")
        self.project_choice = cps.Choice("Project:", [""] , doc = "choose project")        
        self.exp_choice = cps.Choice("Exp:", [""], doc = "choose experiment")
        self.plate_choice = cps.Choice("Plate:", [""], doc = "choose plate")
        self.well_choice = cps.Choice("Well:", [""], doc = "choose well")
        self.site_choice = cps.Choice("Site:", [""], doc = "choose site")
        self.refresh_button = cps.DoSomething("Refresh filter","Refresh", self.refresh_filter)
        self.confirm_button = cps.DoSomething("Confirm filter","Confirm", self.confirm_filter)        
        self.filterlist={"project":"","exp":"","plate":"","well":"","site":""}
        self.cache_loc = cps.DirectoryPath("cache location")
        
        self.imgpathinfo={}        
        self.pathnames = []
        for xx in range(0, 4):
            group = cps.SettingsGroup()
            chind=xx+1
            group.append("image_name",cps.ImageNameProvider("Channel "+str(chind),"ch"+str(chind), doc = "channel "+str(chind)))
            self.pathnames.append(group)
    
    def settings(self):
        result = [self.config_usr, self.config_pwd]
        result += [self.project_choice, self.exp_choice, self.plate_choice,self.well_choice,self.site_choice]
        result += [self.cache_loc]
        for group in self.pathnames:
            result += [group.image_name] 
        return result
    
    
    def visible_settings(self):
        result = [self.config_usr, self.config_pwd]
        result += [self.project_choice, self.exp_choice, self.plate_choice,self.well_choice,self.site_choice]
        result += [self.refresh_button,self.confirm_button]
        result += [self.cache_loc]
        for group in self.pathnames:
            result += [group.image_name]
        return result
    
    def confirm_filter(self):
        self.imgpathinfo={}
        print "filter confirmed"
        print self.project_choice.value
        print self.exp_choice.value
        print self.plate_choice.value
        print self.well_choice.value
        print self.site_choice.value
        if(self.project_choice.value!=""):
            print "project not empty"
            if(self.exp_choice.value!="*"):
                print "one exp in the project"
            else:
                print "all exp in the project"
        else:
            print "project empty"
        
        for i, group in enumerate(self.pathnames):#for each channel
            imgname=group.image_name.value
            self.imgpathinfo[imgname]=allpaths
        
        
        
    
    def refresh_filter(self):
        str_usr = self.config_usr.value;
        str_pwd = self.config_pwd.value;
        
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
        

    
    def prepare_run(self, workspace):
        measurements = workspace.measurements
        
        #start of grouping
        #the grouping is a total mess in cellprofiler. For some reason, keys in set object are completely reversed. An extra correction is made and mapping is remade. 
        key, groupings = self.get_groupings(workspace)#make dictionary
        totalgroup = len(groupings)
        img_grp_map={}
        img_grp_map_ind={};
        group_number = 0
        for group_key, image_numbers in groupings:#for each group
            group_index = 0
            group_number = group_number+1
            rev_group_number = totalgroup - group_number + 1#the set sorts the key reversely            
            project, exp, plate, well, site  = [group_key[k] for k in C_GROUP_TAG_PROJECT, C_GROUP_TAG_EXP, C_GROUP_TAG_PLATE, C_GROUP_TAG_WELL, C_GROUP_TAG_SITE]
            
            print project, exp, plate, well, site, "grp:"+str(rev_group_number)
            for ii, curpath in enumerate(allpaths):#for each image
                if allprojects[ii] == project and allexps[ii] == exp and allplates[ii] == plate and allwells[ii] == well and allsites[ii] == site:
                    group_index += 1
                    img_grp_map[ii]=rev_group_number#given the image the reversed group number
                    img_grp_map_ind[ii]=group_index#the group index is correct
        #end of grouping
        
        print "group_number:", img_grp_map
        print "group_index:", img_grp_map_ind
        for ii in range(0, nrimage):#for each image
            image_number = ii+1
            group_number = img_grp_map[ii]
            group_index = img_grp_map_ind[ii]
            project = allprojects[ii]
            exp = allexps[ii]
            plate = allplates[ii]
            well = allwells[ii]
            site = allsites[ii]
            
            for i, group in enumerate(self.pathnames):#for each channel
                #print group.image_name.value                        
                filenames=self.imgpathinfo[group.image_name.value]
                filename=filenames[ii]
                
                cachepathname = self.cache_loc.get_absolute_path()
                
                if not os.path.exists(cachepathname):
                    os.makedirs(cachepathname)
                
                path = os.path.join(cachepathname, filename)
                #print path#checking input   
                filename_feature = C_FILE_NAME + "_" + group.image_name.value
                pathname_feature = C_PATH_NAME + "_" + group.image_name.value                
                measurements.add_measurement(cpmeas.IMAGE, pathname_feature, cachepathname, image_set_number = image_number)
                measurements.add_measurement(cpmeas.IMAGE, filename_feature, filename, image_set_number = image_number)
                
            measurements.add_measurement(cpmeas.IMAGE, cpmeas.GROUP_NUMBER, group_number, image_set_number = image_number)
            measurements.add_measurement(cpmeas.IMAGE, cpmeas.GROUP_INDEX, group_index, image_set_number = image_number)
            measurements.add_measurement(cpmeas.IMAGE, C_GROUP_TAG_PROJECT, project, image_set_number = image_number)
            measurements.add_measurement(cpmeas.IMAGE, C_GROUP_TAG_EXP, exp, image_set_number = image_number)
            measurements.add_measurement(cpmeas.IMAGE, C_GROUP_TAG_PLATE, plate, image_set_number = image_number)
            measurements.add_measurement(cpmeas.IMAGE, C_GROUP_TAG_WELL, well, image_set_number = image_number)
            measurements.add_measurement(cpmeas.IMAGE, C_GROUP_TAG_SITE, site, image_set_number = image_number)
                
        return True
    
    def run(self, workspace):
        measurements = workspace.measurements
        for i, group in enumerate(self.pathnames):
            imgname = group.image_name.value            
            filename_feature = C_FILE_NAME + "_" + group.image_name.value
            pathname_feature = C_PATH_NAME + "_" + group.image_name.value
            pathname = measurements.get_measurement(cpmeas.IMAGE, pathname_feature)
            filename = measurements.get_measurement(cpmeas.IMAGE, filename_feature)
            grpind = measurements.get_measurement(cpmeas.IMAGE, cpmeas.GROUP_INDEX)
            fext=os.path.splitext(filename)[1]
            tempfilename = tempfile.mktemp(prefix="seq_"+format(grpind, '08d')+"_",suffix= fext,dir=pathname)                        
            localpath = os.path.join(pathname, tempfilename)
            #print path
                
            script = """
            importPackage(Packages.ij);        
            strclasspath=java.lang.System.getProperty("java.class.path");
            var conn=new Packages.SFTP.SFTPConn(usr,pwd,host,port);
            conn.get(remotepath,localpath);
            """
            remotepath=remoteroot+filename
            jsinputs={"remotepath":remotepath,
                      "localpath":localpath,
                      "usr":usr,
                      "pwd":pwd,
                      "host":host,
                      "port":port};
            jb.run_script(script,bindings_in=jsinputs)
            
            data = load_using_bioformats(localpath)        
            image = cpi.Image(data)
            workspace.image_set.add(group.image_name.value, image)
              
            os.remove(localpath)     

        return True
    
    def get_groupings(self, workspace):
        d = {}
        grp_number=0;
        for iii,path in enumerate(allpaths):
            key = (str(allprojects[iii]), str(allexps[iii]), str(allplates[iii]), str(allwells[iii]), str(allsites[iii]))
            print "key:", key
            #print iii,key
            if key not in d:
                d[key] = 0
            d[key] = d[key] + 1
            
        
        print d#somehow the key is reversed
        groupings = []
        image_number = 1
        for project, exp, plate, well, site in d.keys():
            
            group_key = { C_GROUP_TAG_PROJECT:project,
                          C_GROUP_TAG_EXP:exp,
                          C_GROUP_TAG_PLATE:plate,
                          C_GROUP_TAG_WELL:well, 
                          C_GROUP_TAG_SITE:site }
            #print group_key
            group_image_numbers = range(image_number, d[project, exp, plate, well, site] + image_number)
            image_number += d[project, exp, plate, well, site]
            groupings.append((group_key, group_image_numbers))
        
        #print groupings
        return (C_GROUP_TAG_PROJECT, C_GROUP_TAG_EXP, C_GROUP_TAG_PLATE, C_GROUP_TAG_WELL, C_GROUP_TAG_SITE), groupings

    def is_load_module(self):
        return True
    
    def get_measurement_columns(self, pipeline):
        #make tags available for the whole pipeline
        return [(cpmeas.IMAGE, C_GROUP_TAG_PROJECT, cpmeas.COLTYPE_VARCHAR),
                (cpmeas.IMAGE, C_GROUP_TAG_EXP, cpmeas.COLTYPE_VARCHAR),
                (cpmeas.IMAGE, C_GROUP_TAG_PLATE, cpmeas.COLTYPE_VARCHAR),
                (cpmeas.IMAGE, C_GROUP_TAG_WELL, cpmeas.COLTYPE_VARCHAR),
                (cpmeas.IMAGE, C_GROUP_TAG_SITE, cpmeas.COLTYPE_VARCHAR)]