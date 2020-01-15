#!/usr/bin/env python3

import sys
import re

class Edid:
    def __init__(self, edid_array):
        # header information
        self.header              = edid_array[0:8]
        self.manufacturer_id     = edid_array[8:10]
        self.product_code        = edid_array[10:12]
        self.serial_no           = edid_array[12:16]
        self.manufacture_week    = edid_array[16]
        self.manufacture_year    = edid_array[17]
        self.edid_version        = edid_array[18:20]

        # basic display parameters [20-24]
        self.input_params_bitmap = edid_array[20]
        self.h_size_cm           = edid_array[21]
        self.v_size_cm           = edid_array[22]
        self.gamma               = edid_array[23]
        self.features_bitmap     = edid_array[24]

        # chromaticity co-ordinates [25-34]
        self.chroma_coords       = edid_array[25:35]
        # established timing bitmap [35-37]
        self.est_timing_bitmap   = edid_array[35:38]

        # standard timing information [38-53]
        self.display_modes       = edid_array[38:54]

        self.descriptor1         = edid_array[54:72]
        self.descriptor2         = edid_array[72:90]
        self.descriptor3         = edid_array[90:108]
        self.descriptor4         = edid_array[108:126]

        self.num_extensions      = edid_array[126]
        self.checksum            = edid_array[127]

def format_edid_chunk(chunk):
    if isinstance(chunk, list):
        return re.sub('(\S\S)', '0x\g<1>', ' '.join(chunk))
    else:
        return re.sub('(\S\S)', '0x\g<1>', ' '.join([chunk]))

def parse_header(header):
    return 'Valid' if header == ['00', 'FF', 'FF', 'FF', 'FF', 'FF', 'FF', '00'] else 'Invalid'

def parse_mfct_id(code):
    id_hex = int(''.join(code), base=16)
    char1  = chr(((id_hex >> 00) & (0x001F)) + 0x40)
    char2  = chr(((id_hex >>  5) & (0x001F)) + 0x40)
    char3  = chr(((id_hex >> 10) & (0x001F)) + 0x40)

    return ''.join([char3, char2, char1])

def parse_year(year):
    return 1990 + int(year, base = 16)

def parse_week(week):
    return int(week, base=16)

def parse_edid_ver(ver):
    if ver[0] == '01':
        return '1.{}'.format(int(ver[1]))
    else:
        return '??'

def parse_input_params(params):
    params = int(params, base=16)
    if (params >> 7) == 0x1: # digital
        bitdepth = ((params >> 4) & 0x7) * 2 + 4
        input_type = (params & 0x7)
        if input_type == 2:
            interface = 'HDMIa'
        elif input_type == 3:
            interface = 'HDMIb'
        elif input_type == 4:
            interface = 'MDDI'
        elif input_type == 5:
            interface = 'DisplayPort'
        else:
            interface = 'Unknown'
        return 'Digital, {} bit colour, {}'.format(bitdepth, interface)
    else: # analog
        return 'Analog'

def parse_size(size):
    return int(size, base=16)

def parse_gamma(gamma):
    return (int(gamma, base=16) + 100) / 100

def parse_features(features):
    features = int(features, base=16)
    feature_list = ['']
    feature_list.append('    DPMS standby {}supported'.format('un' if not ((features >> 7) & 0x1) else ''))
    feature_list.append('    DPMS suspend {}supported'.format('un' if not ((features >> 6) & 0x1) else ''))
    feature_list.append('    DPMS active-off {}supported'.format('un' if not ((features >> 5) & 0x1) else ''))

    display_type = (features >> 3) & 0x3
    if display_type == 0x00:
        feature_list.append('    RGB 4:4:4')
    elif display_type == 0x01:
        feature_list.append('    RGB 4:4:4 + YCrCb 4:4:4')
    elif display_type == 0x02:
        feature_list.append('    RGB 4:4:4 + YCrCb 4:2:2')
    elif display_type == 0x02:
        feature_list.append('    RGB 4:4:4 + YCrCb 4:2:2 + YCrCb 4:2:2')

    feature_list.append('    {}Standard sRGB colourspace'.format('Non-' if not ((features >> 2) & 0x1) else ''))
    feature_list.append('    Native pixel format and refresh rate {} first DTD'.format('not in' if not ((features >> 1) & 0x1) else 'in'))
    feature_list.append('    Continuous timings (GVT or CVT) {}supported'.format('un' if not ((features >> 0) & 0x1) else ''))
    return '\n'.join(feature_list)

class chroma_coords:
    def __init__(self, chr_coords):
        coords  = [int(c, base=16) for c in chr_coords]
        rg_lsbs = coords[0]
        bw_lsbs = coords[1]
        r_msb   = coords[2:4]
        g_msb   = coords[4:6]
        b_msb   = coords[6:8]
        w_msb   = coords[8:10]

        rx_lsbs = (rg_lsbs >> 6) & 0x3
        ry_lsbs = (rg_lsbs >> 4) & 0x3
        gx_lsbs = (rg_lsbs >> 2) & 0x3
        gy_lsbs = (rg_lsbs >> 0) & 0x3
        bx_lsbs = (bw_lsbs >> 6) & 0x3
        by_lsbs = (bw_lsbs >> 4) & 0x3
        wx_lsbs = (bw_lsbs >> 2) & 0x3
        wy_lsbs = (bw_lsbs >> 0) & 0x3

        rx_msbs = r_msb[0]
        ry_msbs = r_msb[1]
        gx_msbs = g_msb[0]
        gy_msbs = g_msb[1]
        bx_msbs = b_msb[0]
        by_msbs = b_msb[1]
        wx_msbs = w_msb[0]
        wy_msbs = w_msb[1]

        self.rx = ((rx_msbs << 2) + rx_lsbs) / 1024
        self.ry = ((ry_msbs << 2) + ry_lsbs) / 1024
        self.gx = ((gx_msbs << 2) + gx_lsbs) / 1024
        self.gy = ((gy_msbs << 2) + gy_lsbs) / 1024
        self.bx = ((bx_msbs << 2) + bx_lsbs) / 1024
        self.by = ((by_msbs << 2) + by_lsbs) / 1024
        self.wx = ((wx_msbs << 2) + wx_lsbs) / 1024
        self.wy = ((wy_msbs << 2) + wy_lsbs) / 1024

def parse_chroma_coords(coords):
    print("    Red  : ({},{})".format(coords.rx, coords.ry))
    print("    Green: ({},{})".format(coords.gx, coords.gy))
    print("    Blue : ({},{})".format(coords.bx, coords.by))
    print("    White: ({},{})".format(coords.wx, coords.wy))

def parse_timings(timings):
    timings0 = int(timings[0], base=16)
    timings1 = int(timings[1], base=16)
    timings2 = int(timings[2], base=16)
    timing_list = [' ']
    timing_list.append('    {}'.format(' 720×400 @ 70 Hz'   if ((timings0 >> 7) & 0x1) else ''))
    timing_list.append('    {}'.format(' 720×400 @ 88 Hz'   if ((timings0 >> 6) & 0x1) else ''))
    timing_list.append('    {}'.format(' 640×480 @ 60 Hz'   if ((timings0 >> 5) & 0x1) else ''))
    timing_list.append('    {}'.format(' 640×480 @ 67 Hz'   if ((timings0 >> 4) & 0x1) else ''))
    timing_list.append('    {}'.format(' 640×480 @ 72 Hz'   if ((timings0 >> 3) & 0x1) else ''))
    timing_list.append('    {}'.format(' 640×480 @ 75 Hz'   if ((timings0 >> 2) & 0x1) else ''))
    timing_list.append('    {}'.format(' 800×600 @ 56 Hz'   if ((timings0 >> 1) & 0x1) else ''))
    timing_list.append('    {}'.format(' 800×600 @ 60 Hz'   if ((timings0 >> 0) & 0x1) else ''))
    timing_list.append('    {}'.format(' 800×600 @ 72 Hz'   if ((timings1 >> 7) & 0x1) else ''))
    timing_list.append('    {}'.format(' 800×600 @ 75 Hz'   if ((timings1 >> 6) & 0x1) else ''))
    timing_list.append('    {}'.format(' 832×624 @ 75 Hz'   if ((timings1 >> 5) & 0x1) else ''))
    timing_list.append('    {}'.format('1024×768 @ 87 Hz'  if ((timings1 >> 4) & 0x1) else ''))
    timing_list.append('    {}'.format('1024×768 @ 60 Hz'  if ((timings1 >> 3) & 0x1) else ''))
    timing_list.append('    {}'.format('1024×768 @ 70 Hz'  if ((timings1 >> 2) & 0x1) else ''))
    timing_list.append('    {}'.format('1024×768 @ 75 Hz'  if ((timings1 >> 1) & 0x1) else ''))
    timing_list.append('    {}'.format('1280×1024 @ 75 Hz' if ((timings1 >> 0) & 0x1) else ''))
    timing_list.append('    {}'.format('1152x870 @ 75 Hz ' if ((timings2 >> 7) & 0x1) else ''))

    return '\n'.join([l for l in timing_list if l != '    '])

def parse_display_modes(display_modes):
    mode_list = ['']
    modes = [
                display_modes[ 0 : 2],
                display_modes[ 2 : 4],
                display_modes[ 4 : 6],
                display_modes[ 6 : 8],
                display_modes[ 8 :10],
                display_modes[10 :12],
                display_modes[12 :14],
                display_modes[14 :16]
            ]

    for mode in modes:
        if not mode == ['01', '01']:
            h_res = (int(mode[0], base=16) + 31) * 8
            asp_ratio_hex = int(mode[1], base=16) >> 6
            if asp_ratio_hex == 0:
                asp_ratio = 1.6
            elif asp_ratio_hex == 1:
                asp_ratio = 4/3
            elif asp_ratio_hex == 2:
                asp_ratio = 5/4
            elif asp_ratio_hex == 3:
                asp_ratio = 16/9
            v_res = round(h_res / asp_ratio)

            v_freq = (int(mode[1], base=16) & 0x3F) + 60
            mode_list.append('    {}x{:4} @ {}Hz'.format(h_res, v_res, v_freq))

    return '\n'.join(mode_list)

#def parse_dtds(dtds_string):
#    dtds_int = [int(i, base=16) for i in dtds_string]
#
#    pixel_clock =

class descriptor:
    def __init__(self, desc_string):
        self.desc_raw = desc_string
        desc_int = [int(i, base=16) for i in desc_string]
        if not (desc_int[0] == 0 and desc_int[1] == 0):
            self.desctype       = 'dtd'
            self.pxlclk_MHz = ((desc_int[0] << 8) + desc_int[1]) / 100
            self.h_active   = desc_int[2] + ((desc_int[4] >> 4) & 0xF)
            self.h_blank    = desc_int[3] + ((desc_int[4] >> 0) & 0xF)
            self.v_active   = desc_int[5] + ((desc_int[7] >> 4) & 0xF)
            self.v_blank    = desc_int[6] + ((desc_int[7] >> 0) & 0xF)
            self.h_fporch   = desc_int[8] + ((desc_int[11]>> 6) & 0x3)
            self.h_syncpulse= desc_int[9] + ((desc_int[11]>> 4) & 0x3)
            self.v_fporch   = ((desc_int[10] >> 4) & 0xF) + ((desc_int[11]>> 2) & 0x3)
            self.v_syncpulse= ((desc_int[10] >> 0) & 0xF) + ((desc_int[11]>> 0) & 0x3)
            self.h_size_mm  = desc_int[12]+ ((desc_int[14]>> 4) & 0xF)
            self.v_size_mm  = desc_int[13]+ ((desc_int[14] >> 0) & 0xF)
            self.h_border   = desc_int[15]
            self.v_border   = desc_int[16]
            self.features   = desc_int[17]
        else:
            self.desctype   = "display descriptor"

def parse_dtd(dtd):
    print("    Pixel clock                = {}MHz".format(dtd.pxlclk_MHz))
    print("    Horizontal active          = {}".format(dtd.h_active))
    print("    Horizontal blank           = {}".format(dtd.h_blank))
    print("    Vertical active            = {}".format(dtd.v_active))
    print("    Vertical blank             = {}".format(dtd.v_blank))
    print("    Horizontal front porch     = {}".format(dtd.h_fporch))
    print("    Horizontal sync pulse      = {}".format(dtd.h_syncpulse))
    print("    Vertical front porch       = {}".format(dtd.v_fporch))
    print("    Vertical sync pulse        = {}".format(dtd.v_syncpulse))
    print("    Horizontal image size (mm) = {}".format(dtd.h_size_mm))
    print("    Vertical image size (mm)   = {}".format(dtd.v_size_mm))
    print("    Horizontal border          = {} ({} total)".format(dtd.h_border, 2*dtd.h_border))
    print("    Vertical border            = {} ({} total)".format(dtd.v_border, 2*dtd.v_border))
    print("    {}".format(dtd.desc_raw))


def parse_edid(edid):
    print("Header              = {} ({})".format(parse_header(edid.header), format_edid_chunk(edid.header)))
    print("Manufacturer ID     = {} ({})".format(parse_mfct_id(edid.manufacturer_id), format_edid_chunk(edid.manufacturer_id)))
    print("Product code        = {}".format(format_edid_chunk(edid.product_code)))
    print("Serial no           = {}".format(format_edid_chunk(edid.serial_no)))
    print("Manufacture week    = {:02} ({})".format(parse_week(edid.manufacture_week), format_edid_chunk(edid.manufacture_week)))
    print("Manufacture year    = {} ({})".format(parse_year(edid.manufacture_year), format_edid_chunk(edid.manufacture_year)))
    print("Edid version        = {} ({})".format(parse_edid_ver(edid.edid_version),(format_edid_chunk(edid.edid_version))))

    print("Input parameters    = {} ({})".format(parse_input_params(edid.input_params_bitmap), format_edid_chunk(edid.input_params_bitmap)))
    print("H size cm           = {} ({})".format(parse_size(edid.h_size_cm), format_edid_chunk(edid.h_size_cm)))
    print("V size cm           = {} ({})".format(parse_size(edid.v_size_cm), format_edid_chunk(edid.v_size_cm)))
    print("Gamma               = {} ({})".format(parse_gamma(edid.gamma),format_edid_chunk(edid.gamma)))
    print("Features            = {} ({})".format(parse_features(edid.features_bitmap), format_edid_chunk(edid.features_bitmap)))

    print('\n')
    print("Chromaticity co-ordinates = ")
    parse_chroma_coords(chroma_coords(edid.chroma_coords))

    print('\n')
    print("Established timing  = {} ({})".format(parse_timings(edid.est_timing_bitmap), format_edid_chunk(edid.est_timing_bitmap)))

    print('\n')
    print("Display modes = {} ({})".format(parse_display_modes(edid.display_modes),format_edid_chunk(edid.display_modes)))

    descriptors = []
    descriptors.append(descriptor(edid.descriptor1))
    descriptors.append(descriptor(edid.descriptor2))
    descriptors.append(descriptor(edid.descriptor3))
    descriptors.append(descriptor(edid.descriptor4))

    for i in range(1,5):
        if descriptors[i-1].desctype == 'dtd':
            print('\n')
            print("Detailed Timing Descriptor {}".format(i))
            parse_dtd(descriptors[i-1])

    print('\n')
    print("Num extensions      = {}".format(format_edid_chunk(edid.num_extensions)))
    print("Checksum            = {}".format(format_edid_chunk(edid.checksum)))

## begin

with open(sys.argv[1], 'r') as edid_file:
    # the idea here is to remove any formatting likely to be present in a
    # supplied edid - commas, 0x prefix, spaces, newlines. We then put the
    # spaces back in, so the EDID is in a known state
    edid_raw = edid_file.read()
    edid_raw = re.sub('\s', '', edid_raw)
    edid_raw = re.sub(',', '', edid_raw)
    edid_raw = re.sub('0x', '', edid_raw)
    edid_raw = re.sub('(..)', '\g<1> ', edid_raw)
    edid_formatted = edid_raw.split()[0:128]
    edid = Edid(edid_formatted)
    parse_edid(edid)
