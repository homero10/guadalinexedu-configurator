#! /usr/bin/python
# -*- coding: utf-8 -*-

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio
import signal
import subprocess
import shlex
import os
import shutil

class GEDUConfig(Gtk.Window):

    def execute(self, command):
        args = shlex.split(command)
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        out, err = p.communicate()
        return out, err

    def isGeduSlim(self):
        out = subprocess.call("dpkg -l guadalinexedu-educacion-slim 2> /dev/null 1> /dev/null", shell=True)
        if out == 0:
            return True
        else:
            return False

    def AutologinStatus(self):
        # Commands to execute for MD5 checksums
        withautologin = "md5sum /usr/share/cga/cga-lightdm-config/lightdm-autologin.conf"
        withoutautologin = "md5sum /usr/share/cga/cga-lightdm-config/lightdm.conf"
        status = "md5sum /etc/lightdm/lightdm.conf"

        # Execution of the command
        md5with, _ = self.execute(withautologin)
        md5without, _ = self.execute(withoutautologin)
        md5config, _ = self.execute(status)

        # Strip only MD5 checksums
        md5with = ''.join(md5with).split(' ')[0]
        md5without = ''.join(md5without).split(' ')[0]
        md5config = ''.join(md5config).split(' ')[0]

        if md5config == md5with:
            return True
        elif md5config == md5without:
            return False
        else:
            return False

    def DateStatus(self):
        # Long date is active:
        out, err = self.execute("gsettings get org.gnome.desktop.interface clock-show-date")
        if out == 'true\n':
            return True
        else:
            return False


    def BotonesVentanaStatus(self):
        # Si los botones están activados en la parte derecha:
        out, err =  self.execute("gsettings set org.gnome.desktop.wm.preferences button-layout")
        if out == "':minimize,maximize,close\n'":
            return True
        else:
            return False


    def FileExplorerStatus(self):
        # List view is active:
        out, err = self.execute("gsettings get org.gnome.nautilus.preferences default-folder-viewer")
        if out == "'list-view\n'":
            return True
        else:
            return False


    def on_botones_ventana_switch_changed(self, switch, gparam):
        # Si los botones están en el lado derecho:
        if self.BotonesVentanaStatus() == True:
            # Cambiando la posición de los botones
            self.execute("gsettings set org.gnome.desktop.wm.preferences button-layout 'close,maximize,minimize:' ")
        # Si los botones están en el lado izquierdo:
        else:
            # Se cambia al lado derecho:
            self.execute("gsettings set org.gnome.desktop.wm.preferences button-layout ':minimize,maximize,close' ")


    def on_file_explorer_switch_changed(self, switch, gparam):
        # Long date is active:
        if self.FileExplorerStatus() == True:
            # Deactivating long date
            self.execute("gsettings set org.gnome.nautilus.preferences default-folder-viewer 'icon-view' ")
        # Long date isn't active:
        else:
            # Activating long date
            self.execute("gsettings set org.gnome.nautilus.preferences default-folder-viewer 'list-view' ")


    def on_date_switch_changed(self, switch, gparam):
        # Long date is active:
        if self.DateStatus() == True:
            # Deactivating long date
            self.execute("gsettings set org.gnome.desktop.interface clock-show-date false")
        # Long date isn't active:
        else:
            # Activating long date
            self.execute("gsettings set org.gnome.desktop.interface clock-show-date true")

    def on_autologin_switch_changed(self, switch, gparam):
        # Autologin is active in lightdm.conf:
        if self.AutologinStatus() == True:
            # Deactivating autologin
            self.execute("sudo /usr/share/guadalinexedu-configurator/setautologin deactivate")
        # Autologin isn't active in lightdm.conf:
        else:
            # Activating autologin
            self.execute("sudo /usr/share/guadalinexedu-configurator/setautologin activate")


    def button_dd_clicked_cb(self, widget, data = None):
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.WARNING, Gtk.ButtonsType.OK_CANCEL, "Restauración del escritorio Guadalinex Edu")
        dialog.format_secondary_text("El proceso de restauración borrará cualquier configuración realizada sobre el escritorio, como por ejemplo el cambio de fondo de escritorio o el tema de colores. Despues de la restauración la aplicación le solicitará reiniciar la sesión de usuario para aplicar los cambios. Si desea continuar pulse el botón Aceptar.")
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.restore_default_desktop()

        dialog.destroy()


    def restore_default_desktop(self):
        pathskel = '/etc/skel'
        homedir = os.getenv("HOME")
        pathfiles_skel = os.listdir(pathskel)
        for entry in pathfiles_skel:
            if os.path.isdir('%s/%s' % (pathskel, entry)):
                if os.path.isdir('%s/%s' % (homedir, entry)):
                    shutil.rmtree('%s/%s' % (homedir, entry))
                shutil.copytree('%s/%s' % (pathskel, entry), '%s/%s' % (homedir, entry))
            elif os.path.isfile('%s/%s' % (pathskel, entry)):
                if os.path.isfile('%s/%s' % (homedir, entry)):
                    os.remove('%s/%s' % (homedir, entry))
                shutil.copy('%s/%s' % (pathskel, entry), homedir)

        try:
            lxsessionpid = os.environ['_LXSESSION_PID']
            self.execute("kill -TERM %s" % lxsessionpid)
        except KeyError:
            self.execute('gnome-session-quit')

    def __init__(self):
        """ Class init event """
        # Setup the window with title and border width.
        Gtk.Window.__init__(self, type=Gtk.WindowType.TOPLEVEL,
                                  title="Configurador de Escritorio de Guadalinex Edu",
                                  resizable=False,
                                  border_width=10)

        # Create a Vertical child box.
        vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)

        # Create and bind the Gtk Switch with the gsettings schema and its key.
        # volumes-visible path in nautilus.desktop schema
        # ----------------------------------------------------------------------- No volumes veisible switch in Xenial version
        # ----------------------------------------------------------------------- G9Slim: The schema org.gnome.nautilus.gschema.xml
        #                                                                                 isn't installed in slim version. As workaround,
        #                                                                                 put nautilus-data as dependency.
        # nautilus_desktop_switch = Gtk.Switch()
        # nautilus_desktop_setting = Gio.Settings.new("org.gnome.nautilus.desktop")
        # nautilus_desktop_setting.bind("volumes-visible", nautilus_desktop_switch, "active", Gio.SettingsBindFlags.DEFAULT)

        # Create the label for the volumes visible switch
        volumes_visible_label = Gtk.Label("Mostrar en el escritorio los volúmenes montados")

        # Create the long date switch
        date_switch = Gtk.Switch()
        date_switch.set_active(self.DateStatus())
        date_switch.connect("notify::active", self.on_date_switch_changed)

        # Create the label for the long date switch
        date_label = Gtk.Label("Mostrar fecha larga en el panel superior")

        # Creamos el switch para la posición de los botones
        button_switch = Gtk.Switch()
        button_switch.set_active(self.BotonesVentanaStatus())
        button_switch.connect("notify::active", self.on_botones_ventana_switch_changed)

        # Nombre del switch
        button_label = Gtk.Label("Botones en las ventanas: posición derecha")


        # Create the long date switch
        file_switch = Gtk.Switch()
        file_switch.set_active(self.FileExplorerStatus())
        file_switch.connect("notify::active", self.on_file_explorer_switch_changed)

        # Create the label for the long date switch
        file_label = Gtk.Label("Navegador de archivos: Vista lista detallada")

        # Position the Switch and its Label inside a Horizontal child box.
        # ----------------------------------------------------------------------- No volumes veisible switch in Xenial version
        # box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 40)
        # box.pack_start(volumes_visible_label, False, False, 10)
        # box.pack_end(nautilus_desktop_switch, False, False, 10)
        # vbox.pack_start(box, False, False, 0)

        box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 40)
        box.pack_start(date_label, False, False, 10)
        box.pack_end(date_switch, False, False, 10)
        if self.isGeduSlim() == False:
            vbox.pack_start(box, False, False, 1)

        boxfile = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 40)
        boxfile.pack_start(file_label, False, False, 10)
        boxfile.pack_end(file_switch, False, False, 10)
        if self.isGeduSlim() == False:
            vbox.pack_start(boxfile, False, False, 1)

        boxbutton = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 40)
        boxbutton.pack_start(button_label, False, False, 10)
        boxbutton.pack_end(button_switch, False, False, 10)
        if self.isGeduSlim() == False:
            vbox.pack_start(boxbutton, False, False, 1)

        # Create the autologin switch
        autologin_switch = Gtk.Switch()
        autologin_switch.set_active(self.AutologinStatus())
        autologin_switch.connect("notify::active", self.on_autologin_switch_changed)

        # Create the label for the autologin switch
        autologin_label = Gtk.Label("Login automático para el usuario \"usuario\"")

        # Position the Switch and its Label inside a Horizontal child box.
        # ----------------------------------------------------------------------- No volumes veisible switch in Xenial version
        # box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 40)
        # box.pack_start(volumes_visible_label, False, False, 10)
        # box.pack_end(nautilus_desktop_switch, False, False, 10)
        # vbox.pack_start(box, False, False, 0)

        box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 40)
        box.pack_start(autologin_label, False, False, 10)
        box.pack_end(autologin_switch, False, False, 10)
        vbox.pack_start(box, False, False, 1)

	# Bloque para incluir el restaurador de escritorio
        box_dd = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 40)
	label_dd = Gtk.Label("Restaurar el escritorio por defecto de Guadalinex Edu")
	button_dd = Gtk.Button("Ejecutar")
	button_dd.connect("clicked", self.button_dd_clicked_cb)
	box_dd.pack_start(label_dd, False, False, 10)
	box_dd.pack_start(button_dd, False, False, 10)
	vbox.pack_start(box_dd, False, False, 1)

        # Add the child box to the window
        self.add(vbox)
        self.connect("destroy", Gtk.main_quit)
        signal.signal(signal.SIGINT, signal.SIG_DFL)

if __name__ == "__main__":
    window = GEDUConfig()
    window.set_position(Gtk.WindowPosition.CENTER)
    window.show_all()
    Gtk.main()
