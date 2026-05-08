import storage
import usb_cdc
import usb_hid

storage.disable_usb_drive()
usb_cdc.disable()
usb_hid.enable((usb_hid.Device.KEYBOARD,))
