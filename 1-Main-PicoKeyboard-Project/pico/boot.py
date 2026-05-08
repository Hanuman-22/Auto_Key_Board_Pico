import usb_hid

# Enable keyboard. Storage stays ON.
usb_hid.enable((usb_hid.Device.KEYBOARD,))
