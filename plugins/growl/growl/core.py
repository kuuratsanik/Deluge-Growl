#
# core.py
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#
#

from twisted.internet import defer
from twisted.internet import reactor

from deluge.log import LOG as log
from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export

from socket import AF_INET, SOCK_DGRAM, socket
from growlapi.growl import GrowlRegistrationPacket
from growlapi.growl import GrowlNotificationPacket

from gntp.notifier import GrowlNotifier

DEFAULT_PREFS = {
    "growl_host": "localhost",
    "growl_password": "",
    "growl_port": 23053,
    "growl_torrent_completed": True,
    "growl_torrent_added": True,
    "growl_sticky": False,
    "growl_priority": 0
}

class Core(CorePluginBase):
    
    def growlInit(self):
        
#        addr = (self.config['growl_host'], self.config['growl_port'])
#        s = socket(AF_INET,SOCK_DGRAM)
#        p = GrowlRegistrationPacket("Deluge", self.config['growl_password'])
#        p.addNotification("Download Completed", True)
#        p.addNotification("Torrent Added", True)
#        s.sendto(p.payload(), addr)
#        s.close()

        self.growl = GrowlNotifier(
    		applicationName = "Deluge",
    		notifications = ["Torrent Added", "Download Completed"],
    		defaultNotifications = ["Torrent Added"],
    		hostname = self.config['growl_host'],
    		password = self.config['growl_password'],
    		port = self.config['growl_port'],
    		debug = 0
    	)
    	result = self.growl.register()
    	

    def sendGrowl(self, noteType, title, description, sticky=False, priority=0):
    
#        p = GrowlNotificationPacket(application="Deluge", notification=noteType, title=title, description=description, priority=priority, sticky=sticky, password=self.config['growl_password']);
#        addr = (self.config['growl_host'], self.config['growl_port'])
#        s = socket(AF_INET,SOCK_DGRAM)
#        s.sendto(p.payload(), addr)
#        s.close()
        result = self.growl.notify(
    		noteType = noteType,
    		title = title,
    		description = description,
    		icon = '',
    		sticky = sticky,
    		priority = priority
    	)
        
         
    def enable(self):
        self.config = deluge.configmanager.ConfigManager("growl.conf", DEFAULT_PREFS)
        
        self.growlInit()	    

        #component.get("AlertManager").register_handler("torrent_finished_alert", self.on_torrent_finished)

        d = defer.Deferred()
        # simulate a delayed result by asking the reactor to schedule
        # gotResults in 2 seconds time
        reactor.callLater(2, self.connect_events)

        log.debug("Growl core plugin enabled!")

        return d


    def disable(self):
        log.debug("Growl core plugin disabled!")
        #component.get("AlertManager").deregister_handler(self.on_alert_torrent_finished)
        self.disconnect_events();
        
        self.config.save()

    def update(self):
        pass
        
    def connect_events(self):
        event_manager = component.get("EventManager")
        event_manager.register_event_handler("TorrentFinishedEvent", self.on_torrent_finished)
        event_manager.register_event_handler("TorrentAddedEvent", self.on_torrent_added)
    
    def disconnect_events(self):
        event_manager = component.get("EventManager")
        event_manager.deregister_event_handler("TorrentFinishedEvent", self.on_torrent_finished)
        event_manager.deregister_event_handler("TorrentAddedEvent", self.on_torrent_added)
    

    def on_torrent_added(self, torrent_id):
        if (self.config['growl_torrent_added'] == False):
            return
        try:
          #torrent_id = str(alert.handle.info_hash())
          torrent = component.get("TorrentManager")[torrent_id]
          torrent_status = torrent.get_status({})

          message = _("Added Torrent \"%(name)s\"") % torrent_status
          
          d = defer.maybeDeferred(self.sendGrowl, "Torrent Added", "Torrent Added", message, self.config['growl_sticky'], self.config['growl_priority'])
          #d.addCallback(self._on_notify_sucess, 'email')
          #d.addErrback(self._on_notify_failure, 'email')
          
          return d
        
        except Exception, e:
          log.error("error in alert %s" % e)

    def on_torrent_finished(self, torrent_id):
        if (self.config['growl_torrent_completed'] == False):
            return
        try:
          #torrent_id = str(alert.handle.info_hash())
          torrent = component.get("TorrentManager")[torrent_id]
          torrent_status = torrent.get_status({})

          message = _("Finished Torrent \"%(name)s\"") % torrent_status
          
          d = defer.maybeDeferred(self.sendGrowl, "Download Completed", "Download Finished", message, self.config['growl_sticky'], self.config['growl_priority'])
          #d.addCallback(self._on_notify_sucess, 'email')
          #d.addErrback(self._on_notify_failure, 'email')
          
          return d

        except Exception, e:
          log.error("error in alert %s" % e)

    ### Exported RPC methods ###
    @export
    def set_config(self, config):
        log.debug("saving config: %s" % config)
        for key in config.keys():
            self.config[key] = config[key]
        self.config.save()

    @export
    def get_config(self):
        log.debug("sending config: %s" % self.config.config)
        return self.config.config
