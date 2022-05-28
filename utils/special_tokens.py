import json
import numpy as np
import os

class SpecialTokens:
    """
    Stop words:
    ourselves hers between Between yourself Yourself but But again Again there There about About once Once during During out Out very Very having Having with With they They own Own an An be Be some Some for For do Do its Its yours Yours such Such into Into of Of most Most itself other Other off Off is Is am Am or Or who Who as As from From him Him each Each the The themselves until Until below Below are Are we We these These your Your his His through Through don Don nor Nor me Me were Were her Her more More himself Himself this This down Down should Should our Our their Their while While above Above both Both up Up to To ours had Had she She all All no No when When at At any Any before Before them Them same Same and And been Been have Have in In will Will on On does Does then Then that That because Because what What over Over why Why so So did Did not Not now Now under Under he He you You herself has Has just Just where Where too Too only Only myself which Which those Those after After few Few whom being Being if If theirs my My against Against by By doing Doing it It how How further Further was Was here Here than Than

    """
    def __init__(self, model_hf_path):
        model_hf_path = model_hf_path.replace('allenai/', 'allenai_')
        if model_hf_path == 'bert-large-cased-whole-word-masking':
            full_stop_token, CLS, SEP = 119, 101, 102

            stop_words = {9655, 4364, 1206, 3847, 3739, 26379, 1133, 1252, 1254, 5630, 1175, 1247, 1164, 3517, 1517, 2857, 1219, 1507, 1149, 3929, 1304, 6424, 1515, 5823, 1114, 1556, 1152, 1220, 1319, 13432, 1126, 1760, 1129, 4108, 1199, 1789, 1111, 1370, 1202, 2091, 1157, 2098, 6762, 25901, 1216, 5723, 1154, 14000, 1104, 2096, 1211, 2082, 2111, 1168, 2189, 1228, 8060, 1110, 2181, 1821, 7277, 1137, 2926, 1150, 2627, 1112, 1249, 1121, 1622, 1140, 15619, 1296, 2994, 1103, 1109, 2310, 1235, 5226, 2071, 12219, 1132, 2372, 1195, 1284, 1292, 1636, 1240, 2353, 1117, 1230, 1194, 4737, 1274, 1790, 4040, 16162, 1143, 2508, 1127, 8640, 1123, 1430, 1167, 3046, 1471, 20848, 1142, 1188, 1205, 5245, 1431, 9743, 1412, 3458, 1147, 2397, 1229, 1799, 1807, 12855, 1241, 2695, 1146, 3725, 1106, 1706, 17079, 1125, 6467, 1131, 1153, 1155, 1398, 1185, 1302, 1165, 1332, 1120, 1335, 1251, 6291, 1196, 2577, 1172, 23420, 1269, 14060, 1105, 1262, 1151, 18511, 1138, 4373, 1107, 1130, 1209, 3100, 1113, 1212, 1674, 7187, 1173, 1599, 1115, 1337, 1272, 2279, 1184, 1327, 1166, 3278, 1725, 2009, 1177, 1573, 1225, 2966, 1136, 1753, 1208, 1986, 1223, 2831, 1119, 1124, 1128, 1192, 1941, 1144, 10736, 1198, 2066, 1187, 2777, 1315, 6466, 1178, 2809, 1991, 1134, 5979, 1343, 4435, 1170, 1258, 1374, 17751, 2292, 1217, 6819, 1191, 1409, 19201, 1139, 1422, 1222, 8801, 1118, 1650, 1833, 27691, 1122, 1135, 1293, 1731, 1748, 6940, 1108, 3982, 1303, 3446, 1190, 16062}
            stop_words = stop_words.union(set((22755, 1232, 23567, 20262))) #Do not appear in Wikipedia.
            single_letters_and_punctuation = set(range(1103))

        elif model_hf_path == 'bert-large-uncased':
            full_stop_token, CLS, SEP = 1012, 101, 102
            full_stop_token = None # Don't want to break.

            stop_words = {2049, 9731, 2053, 2054, 2055, 2057, 2058, 2059, 2572, 2061, 2060, 2062, 2064, 2065, 2068, 2069, 2070, 2582, 2073, 2074, 2076, 2077, 2079, 2083, 2084, 2085, 2087, 2090, 2091, 2096, 2097, 2104, 2106, 2107, 2108, 2114, 2115, 2119, 2122, 2123, 2125, 2127, 6737, 2129, 2138, 2151, 2153, 3183, 2168, 2169, 2682, 2182, 3209, 2200, 2205, 2725, 2216, 2219, 2256, 2261, 17156, 2320, 2323, 2841, 2339, 14635, 2870, 2370, 4426, 2383, 2917, 4496, 2993, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2515, 2003, 2005, 2004, 2007, 2006, 2009, 2010, 2011, 2008, 2013, 2012, 2014, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027, 2029, 2030, 2031, 2032, 2033, 5106, 2035, 2037, 2038, 2039, 2040, 2041, 2042, 2043, 2044, 2045, 2046}
            single_letters_and_punctuation = set(range(1996))
            # single_letters_and_punctuation.add(2133) # adding ...
        elif model_hf_path == 'allenai_scibert_scivocab_uncased':
            full_stop_token, UNK, CLS, SEP = 205, 101, 102, 103
            self.UNK = UNK

            stop_words = {20560, 467, 563, 1573, 461, 1011, 3246, 781, 556, 1248, 2773, 190, 698, 2910, 130, 195, 693, 168, 572, 633, 555, 690, 131, 755, 3987, 494, 1874, 165, 439, 234, 975, 188, 263, 6888, 535, 111, 5675, 3088, 2382, 220, 185, 407, 5296, 1972, 833, 3313, 2247, 366, 267, 1750, 475, 17146, 238, 1922, 1055, 580, 547, 969, 1431, 655, 692, 147, 13529, 883, 2281, 355, 425, 603, 235, 843, 1548, 1445, 855, 137, 528, 360, 121, 650, 191, 1452, 666, 198, 923, 1792, 573, 4682, 564, 1544, 302, 1842, 604, 299, 3034, 29210, 434, 3008, 582, 3872, 617, 28738, 334, 1052, 647, 2149, 7861, 1558, 543, 1536, 2089, 214, 8328, 256, 539, 911, 241, 1530, 506}
            do_not_appear_in_cord = set((853, 1233, 1788, 2058, 2176, 2198, 2353, 2369, 2477, 2758, 2814, 2888, 2919, 3106, 3170, 3179, 3215, 3251, 3271, 3338, 3390, 3400, 3482, 3534, 3562, 3569, 3620, 3665, 3693, 3709, 3761, 3847, 3893, 3902, 3914, 3919, 3959, 3969, 4007, 4062, 4186, 4214, 4252, 4287, 4363, 4365, 4370, 4394, 4409, 4414, 4473, 4513, 4526, 4560, 4571, 4575, 4587, 4622, 4643, 4661, 4719, 4726, 4775, 4824, 4840, 4866, 4896, 4906, 4921, 4938, 4974, 5040, 5052, 5202, 5262, 5272, 5362, 5378, 5424, 5496, 5613, 5648, 5661, 5713, 5738, 5822, 5894, 5933, 5937, 5991, 5997, 6007, 6012, 6056, 6085, 6144, 6150, 6171, 6184, 6185, 6195, 6209, 6234, 6245, 6255, 6297, 6324, 6396, 6516, 6620, 6658, 6668, 6681, 6712, 6856, 6866, 6900, 6936, 6974, 7073, 7082, 7087, 7101, 7215, 7250, 7282, 7375, 7383, 7408, 7412, 7502, 7520, 7521, 7527, 7585, 7605, 7680, 7698, 7711, 7807, 7828, 7833, 7844, 7869, 7878, 7895, 7937, 7959, 7969, 8065, 8106, 8131, 8171, 8187, 8194, 8221, 8254, 8255, 8297, 8301, 8324, 8338, 8379, 8413, 8454, 8589, 8743, 8744, 8767, 8769, 8787, 8792, 8815, 8819, 8909, 8921, 8940, 8969, 8987, 9019, 9029, 9056, 9090, 9180, 9220, 9248, 9264, 9315, 9343, 9347, 9352, 9379, 9407, 9452, 9456, 9467, 9498, 9511, 9564, 9621, 9644, 9673, 9678, 9711, 9731, 9738, 9745, 9802, 9854, 9906, 9910, 9929, 9948, 9961, 9987, 10050, 10103, 10106, 10131, 10148, 10196, 10217, 10258, 10264, 10283, 10323, 10344, 10398, 10403, 10464, 10486, 10491, 10506, 10520, 10598, 10732, 10743, 10747, 10748, 10790, 10797, 10799, 10840, 10852, 10856, 10885, 10925, 10937, 10938, 10956, 11027, 11030, 11033, 11075, 11080, 11084, 11094, 11136, 11141, 11219, 11258, 11264, 11267, 11272, 11289, 11354, 11364, 11374, 11409, 11411, 11433, 11473, 11522, 11596, 11621, 11680, 11712, 11717, 11752, 11761, 11782, 11786, 11793, 11855, 11869, 11885, 11887, 11898, 11907, 11927, 11928, 11971, 11973, 11983, 12004, 12011, 12051, 12055, 12116, 12155, 12159, 12161, 12197, 12207, 12224, 12235, 12276, 12283, 12300, 12301, 12322, 12349, 12360, 12368, 12446, 12505, 12536, 12549, 12557, 12584, 12596, 12678, 12690, 12707, 12725, 12728, 12801, 12838, 12851, 12908, 12913, 12923, 12924, 12983, 12989, 13043, 13112, 13128, 13144, 13165, 13172, 13174, 13177, 13197, 13226, 13230, 13253, 13270, 13279, 13289, 13290, 13291, 13322, 13338, 13366, 13395, 13404, 13416, 13427, 13441, 13460, 13539, 13597, 13605, 13616, 13623, 13632, 13656, 13690, 13695, 13747, 13761, 13778, 13785, 13790, 13818, 13820, 13832, 13891, 13931, 13944, 13991, 14098, 14112, 14118, 14119, 14126, 14154, 14160, 14228, 14235, 14267, 14277, 14284, 14304, 14306, 14316, 14323, 14350, 14380, 14383, 14409, 14417, 14422, 14425, 14429, 14438, 14446, 14482, 14514, 14516, 14533, 14573, 14601, 14644, 14653, 14665, 14694, 14695, 14722, 14725, 14726, 14745, 14749, 14755, 14805, 14831, 14884, 14895, 14896, 14912, 14914, 14918, 14995, 15007, 15022, 15084, 15167, 15176, 15212, 15218, 15254, 15266, 15299, 15300, 15348, 15380, 15444, 15466, 15503, 15523, 15549, 15555, 15568, 15575, 15604, 15605, 15618, 15638, 15641, 15732, 15763, 15783, 15786, 15838, 15879, 15883, 15896, 15918, 15941, 15962, 15992, 15997, 16016, 16022, 16025, 16044, 16090, 16105, 16120, 16127, 16140, 16155, 16215, 16216, 16223, 16237, 16239, 16242, 16250, 16294, 16373, 16375, 16386, 16387, 16393, 16421, 16435, 16459, 16502, 16537, 16584, 16608, 16629, 16647, 16654, 16655, 16658, 16670, 16712, 16720, 16729, 16730, 16752, 16762, 16845, 16867, 16889, 16891, 16899, 16917, 16918, 16981, 16999, 17013, 17026, 17037, 17044, 17048, 17091, 17105, 17118, 17134, 17143, 17153, 17176, 17224, 17243, 17255, 17270, 17276, 17290, 17307, 17339, 17358, 17396, 17413, 17458, 17539, 17550, 17563, 17590, 17616, 17643, 17657, 17659, 17666, 17690, 17700, 17711, 17714, 17716, 17725, 17731, 17773, 17792, 17802, 17813, 17844, 17860, 17890, 17896, 17909, 17946, 17965, 17966, 18023, 18061, 18063, 18069, 18075, 18092, 18094, 18120, 18145, 18178, 18228, 18244, 18254, 18288, 18295, 18310, 18329, 18337, 18370, 18384, 18385, 18466, 18470, 18496, 18520, 18531, 18544, 18549, 18562, 18565, 18573, 18577, 18584, 18601, 18615, 18669, 18681, 18765, 18804, 18827, 18847, 18859, 18866, 18867, 18869, 18877, 18898, 18900, 18909, 18918, 18935, 18960, 18980, 19000, 19005, 19013, 19022, 19048, 19050, 19053, 19056, 19064, 19072, 19083, 19105, 19150, 19160, 19165, 19170, 19191, 19194, 19235, 19254, 19282, 19292, 19319, 19320, 19325, 19341, 19372, 19382, 19394, 19409, 19468, 19474, 19503, 19519, 19593, 19606, 19618, 19650, 19677, 19784, 19797, 19811, 19819, 19822, 19844, 19875, 19883, 19884, 19899, 19910, 19936, 19957, 19985, 20022, 20025, 20039, 20059, 20061, 20067, 20069, 20086, 20102, 20123, 20144, 20176, 20195, 20208, 20240, 20245, 20246, 20249, 20250, 20267, 20273, 20307, 20352, 20367, 20372, 20397, 20401, 20404, 20408, 20434, 20438, 20466, 20479, 20483, 20491, 20499, 20519, 20553, 20565, 20608, 20613, 20656, 20670, 20679, 20747, 20750, 20761, 20763, 20774, 20797, 20810, 20815, 20822, 20850, 20856, 20879, 20904, 20922, 20954, 20972, 20996, 20999, 21022, 21047, 21098, 21105, 21113, 21119, 21188, 21192, 21223, 21275, 21291, 21298, 21301, 21305, 21314, 21320, 21328, 21333, 21335, 21383, 21404, 21422, 21446, 21473, 21479, 21488, 21505, 21507, 21510, 21530, 21565, 21592, 21670, 21692, 21731, 21733, 21752, 21792, 21855, 21876, 21907, 21912, 21924, 21955, 21980, 22012, 22027, 22059, 22092, 22107, 22125, 22132, 22138, 22145, 22150, 22153, 22154, 22193, 22214, 22215, 22232, 22245, 22260, 22271, 22279, 22288, 22294, 22299, 22301, 22341, 22360, 22368, 22396, 22401, 22426, 22430, 22444, 22454, 22481, 22489, 22499, 22528, 22530, 22542, 22558, 22588, 22610, 22612, 22626, 22639, 22648, 22672, 22674, 22702, 22730, 22735, 22739, 22748, 22757, 22763, 22769, 22792, 22814, 22880, 22888, 22913, 22984, 23009, 23016, 23032, 23045, 23046, 23068, 23075, 23083, 23086, 23088, 23105, 23133, 23156, 23162, 23173, 23192, 23198, 23230, 23245, 23248, 23266, 23293, 23300, 23307, 23379, 23393, 23401, 23423, 23438, 23485, 23487, 23488, 23514, 23526, 23555, 23558, 23572, 23588, 23604, 23642, 23656, 23672, 23684, 23685, 23721, 23724, 23728, 23748, 23757, 23764, 23799, 23852, 23865, 23872, 23883, 23895, 23984, 24014, 24024, 24044, 24054, 24055, 24084, 24096, 24118, 24185, 24203, 24227, 24234, 24275, 24307, 24318, 24320, 24335, 24363, 24371, 24373, 24402, 24409, 24411, 24432, 24451, 24467, 24484, 24496, 24504, 24523, 24562, 24563, 24589, 24599, 24622, 24685, 24706, 24707, 24729, 24738, 24751, 24767, 24772, 24775, 24792, 24868, 24889, 24893, 24898, 24915, 24917, 24918, 24926, 24948, 24949, 24955, 24961, 24966, 24980, 25045, 25047, 25078, 25085, 25139, 25206, 25208, 25222, 25225, 25232, 25240, 25242, 25243, 25246, 25256, 25291, 25324, 25335, 25355, 25372, 25391, 25393, 25406, 25422, 25440, 25457, 25467, 25520, 25536, 25549, 25588, 25589, 25599, 25615, 25617, 25641, 25664, 25667, 25688, 25690, 25695, 25706, 25760, 25768, 25774, 25780, 25786, 25787, 25818, 25833, 25847, 25916, 25933, 25972, 25994, 25998, 26003, 26015, 26080, 26093, 26117, 26120, 26168, 26176, 26199, 26202, 26210, 26238, 26242, 26244, 26316, 26326, 26331, 26347, 26400, 26407, 26440, 26471, 26502, 26511, 26549, 26552, 26567, 26578, 26603, 26634, 26652, 26681, 26685, 26727, 26739, 26758, 26759, 26794, 26838, 26866, 26879, 26889, 26898, 26928, 26936, 26994, 27003, 27020, 27021, 27084, 27115, 27152, 27172, 27186, 27190, 27196, 27200, 27212, 27257, 27311, 27312, 27324, 27325, 27326, 27333, 27343, 27344, 27353, 27409, 27427, 27471, 27493, 27498, 27509, 27529, 27540, 27547, 27619, 27628, 27654, 27657, 27679, 27707, 27715, 27768, 27796, 27800, 27804, 27859, 27862, 27863, 27896, 27914, 27927, 27933, 28073, 28099, 28127, 28136, 28151, 28179, 28188, 28192, 28193, 28232, 28275, 28288, 28291, 28321, 28346, 28348, 28367, 28377, 28400, 28423, 28438, 28448, 28464, 28470, 28480, 28493, 28530, 28535, 28544, 28546, 28553, 28562, 28574, 28576, 28604, 28616, 28617, 28626, 28631, 28632, 28642, 28650, 28660, 28687, 28700, 28703, 28711, 28719, 28745, 28747, 28773, 28779, 28794, 28816, 28837, 28844, 28849, 28882, 28884, 28891, 28906, 28920, 28935, 28938, 28957, 28985, 28998, 29007, 29017, 29032, 29069, 29085, 29105, 29136, 29193, 29209, 29247, 29360, 29373, 29382, 29384, 29409, 29412, 29480, 29483, 29488, 29500, 29522, 29532, 29547, 29563, 29627, 29658, 29680, 29702, 29719, 29739, 29754, 29766, 29785, 29787, 29791, 29808, 29838, 29843, 29853, 29859, 29889, 29894, 29904, 29913, 29934, 29962, 29970, 29975, 29981, 29988, 30011, 30022, 30033, 30076, 30084, 30090))
            stop_words = stop_words.union(do_not_appear_in_cord)

            single_letters_and_punctuation = {0, 102, 103, 104, 3190, 1554, 3000, 3250, 1863, 894, 2505, 145, 546, 1375, 473, 422, 579, 205, 1352, 244, 158, 170, 239, 286, 305, 370, 450, 493, 514, 862, 1814, 962, 275, 1374, 3912, 5435, 106, 132, 115, 128, 139, 125, 159, 151, 259, 261, 231, 152, 127, 146, 116, 118, 735, 182, 112, 105, 504, 171, 124, 412, 316, 447, 260, 4088, 1901, 7273, 4627, 5114, 106, 132, 115, 128, 139, 125, 159, 151, 259, 261, 231, 152, 127, 146, 116, 118, 735, 182, 112, 105, 504, 171, 124, 412, 316, 447, 1342, 885, 3661, 1709, 13090, 14523, 11221, 20704, 7253, 2703, 12108, 12033, 11025, 3920, 1586, 17984, 1255, 13434, 20226, 106, 106, 106, 106, 106, 28725, 115, 139, 139, 259, 259, 146, 116, 116, 2023, 504, 504, 5024, 16413, 106, 106, 106, 106, 106, 106, 28725, 115, 139, 139, 139, 139, 259, 259, 259, 259, 3861, 146, 116, 116, 116, 116, 116, 26708, 504, 504, 504, 504, 316, 5024, 316, 106, 106, 106, 106, 115, 115, 115, 115, 128, 139, 139, 139, 139, 159, 159, 259, 259, 259, 259, 26497, 152, 152, 152, 146, 146, 146, 116, 116, 116, 116, 182, 112, 112, 112, 112, 112, 112, 105, 105, 105, 504, 504, 504, 504, 504, 504, 124, 316, 447, 447, 447, 447, 447, 116, 504, 106, 259, 116, 504, 116, 112, 112, 105, 105, 1474, 1886, 2416, 2320, 3424, 3827, 2362, 20296, 5715, 1946, 1216, 4484, 2907, 2225, 2699, 2194, 5708, 4477, 3225, 1474, 3424, 3827, 20296, 1474, 1886, 2416, 2320, 3424, 7492, 3827, 2362, 20296, 5715, 1946, 1216, 4484, 4387, 2907, 2853, 2225, 2699, 23529, 2194, 5708, 4477, 3225, 23529, 3225, 17603, 23409, 18984, 25182, 21035, 14620, 17551, 17603, 23409, 18984, 18984, 25182, 21035, 14620, 17551, 28795, 28795, 28795, 22509, 28795, 25258, 27042, 22065, 22120, 19334, 22509, 29000, 128, 151, 151, 151, 151, 231, 127, 146, 146, 182, 112, 105, 106, 106, 106, 106, 106, 106, 106, 139, 139, 139, 139, 139, 259, 116, 116, 116, 116, 116, 116, 116, 116, 504, 504, 504, 504, 504, 504, 504, 316, 316, 1474, 3424, 23529, 1474, 20296, 3827, 20296, 23529, 3225, 23659, 1159, 4123, 23190, 3774, 1384, 5459, 745, 3859, 11619, 8199, 15353, 1480, 1943, 17696, 20801, 10296, 22011, 2402, 25181, 11893, 2371, 1027, 538, 3149, 3809, 4635, 6294, 11858, 6408, 6643, 6874, 275, 6572, 1511, 2345, 6877, 6588, 10174, 10110, 12636, 5824, 29559, 25510, 1064, 1786}

            for i in range(100):
                single_letters_and_punctuation.add(i)
        elif model_hf_path == 'bert-base-chinese':
            full_stop_token, UNK, CLS, SEP = 511, 100, 101, 102
            self.UNK = UNK

            stop_words = {}
            single_letters_and_punctuation = set(range(670))
        else:
            raise NotImplementedError

        self.full_stop_token, self.CLS, self.SEP = full_stop_token, CLS, SEP
        self.stop_words_and_punctuation = stop_words.union(single_letters_and_punctuation)
        # Debug: this file is not provided
        # half_words_list_path = f"non-full-words/non-full-words-{model_hf_path}.npy"
        half_words_list_path = None
        self.half_words_list = np.load(half_words_list_path) if half_words_list_path else []
        lemmatized_vocab_path = f"WSIatScale/lemmatized_vocabs/lemmatized_vocabs-{model_hf_path}.json"
        self.lemmatized_vocab = {int(k): v for k, v in json.load(open(lemmatized_vocab_path, 'r')).items()}

    def valid_token(self, token):
        if token in [self.full_stop_token, self.CLS, self.SEP]:
            return False
        if hasattr(self, 'UNK') and token == self.UNK:
            return False
        if token in self.stop_words_and_punctuation:
            return False
        if token in self.half_words_list:
            return False
        return True

    def full_words_tokens(self, tokenizer):
        vocab = tokenizer.get_vocab()
        ret = set([token for _, token in vocab.items() if self.valid_token(token)])
        return ret

    def lemmatize(self, token):
        # assumes token in self.lemmatized_vocab
        # Debug: this assumption is too strong
        # return self.lemmatized_vocab[token]
        return self.lemmatized_vocab[token] if token in self.lemmatized_vocab.keys() else token

    def tokens_to_annotate(self):
        return set([v for v in self.lemmatized_vocab.values() if self.valid_token(v)])