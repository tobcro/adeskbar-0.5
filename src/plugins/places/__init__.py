# -*- coding: utf-8 -*-
#
#   ADeskBar - "Places" plugin
#   Thanks to : FSnow - fix bug : urllib.unquote (éèà...)
##

import gtk
import os
import urllib

import adesk.plugin as Plg
import adesk.core as Core

class Plugin(Plg.Plugin):
    def __init__(self, bar, settings):
        Plg.Plugin.__init__(self, bar, settings)

    def onClick(self, widget, event):

        def get_position(menu):
            plugin_x, plugin_y, plugin_w, plugin_h = self.get_allocation()
            screen_width, screen_height =  gtk.gdk.screen_width(), gtk.gdk.screen_height()
            menu_size = self.places.menu.size_request()

            padding = 1
            orientation = self.bar.cfg['position']
            
            if orientation == "bottom":
                icon_y = self.bar.bar_pos_y  - menu_size[1] - padding
                icon_x = self.bar.bar_pos_x + plugin_x
            elif orientation == "top":
                icon_y = self.bar.bar_pos_y + self.bar.draw_height + padding
                icon_x = self.bar.bar_pos_x + plugin_x
            elif orientation == "right":
                icon_x = self.bar.bar_pos_x - menu_size[0] - padding
                icon_y = self.bar.bar_pos_y + plugin_y
            elif orientation == "left":
                icon_x = self.bar.bar_pos_x + self.bar.draw_width + padding
                icon_y = self.bar.bar_pos_y + plugin_y

            # Make sure the bottom of the menu doesn't get below the bottom of the screen
            icon_y = min(icon_y, screen_height - menu_size[1])

            return (icon_x, icon_y, False)
            
        self.places = Places(self)
        self.places.menu.popup(None, None, get_position, 0, 0)
        self.is_visible = True


    def resize(self):
        self.set_size_request(self.cfg['icon_size'], self.cfg['icon_size'])

class Places():
    def __init__(self, plugin):
        self.plugin = plugin
        self.menu = gtk.Menu()
        self.menu.connect('deactivate', self.menu_deactivate)

        home = os.environ['HOME']
        
        ### add Home and / (filesystem)
        item = self.append_menu_item(self.menu, 'Home', 'user-home')
        item.connect("activate", self.open_dir, home)
        
        item = self.append_menu_item(self.menu, 'File System', 'drive-harddisk')
        item.connect("activate", self.open_dir, '/')


        ### mounted device : parse /proc/mounts
        mount = []
        
        f = open('/proc/mounts', 'r')

        for l in f:
            if l[0] == '/':
                l = l.split()
                if not l[1] == '/':
                    mount.append(l[1])
        f.close()
        
        if not len(mount) == 0:
            separator = gtk.SeparatorMenuItem()
            self.menu.append(separator)
            separator.show()
            
            for p in mount:
                item = self.append_menu_item(self.menu, p, 'drive-harddisk')
                item.connect("activate", self.open_dir, p)

        ### .gtk-bookmarks - parse user bookmarks
        if os.access("%s/.gtk-bookmarks" % home, os.F_OK|os.R_OK):

            separator = gtk.SeparatorMenuItem()
            self.menu.append(separator)
            separator.show() 

            f = open("%s/.gtk-bookmarks" % home,'r')
            for line in f:
                if line == '\n' or line[0]=='#':
                    continue
                else:
                    line = line.strip('\n')
                    tmp = line.split(' ',1)

                    if len(tmp) >= 2:
                        bm_path = tmp[0].strip(' ')
                        label = tmp[1].strip(' ')
                    else:
                        bm_path = tmp[0].strip(' ')
                        label = tmp[0].split('/')[-1]

                    item = self.append_menu_item(self.menu, urllib.unquote(label), 'folder')
                    item.connect("activate", self.open_dir, bm_path)
            f.close()

    def create_menu_item(self, label, icon_name, comment):
        item = gtk.ImageMenuItem(label)
        item.set_use_underline(0)
        #~ item.props.always_show_image = True
            
        icon_pixbuf = Core.get_pixbuf_icon(icon_name)
        item.set_image(gtk.image_new_from_pixbuf(icon_pixbuf))

        return item

    def append_menu_item(self, menu, label, icon_name, comment=None):
        item = self.create_menu_item(label, icon_name, comment)
        menu.append(item)
        item.show()
        return item

    def open_dir(self, widget, path):
        Core.launch_command('%s "%s"' % (self.plugin.settings['filemanager'], urllib.unquote(path)))

    def menu_deactivate(self, widget):
        self.plugin.is_visible = False
        self.plugin.call_bar_update()
