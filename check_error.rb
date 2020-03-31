require 'orclib'

# PCS_GOPX16_PCS_ERROR_STATUS_dup3/4/5 0x120F0210,
register_map = {0x120F0210 => 'PCS_GOPX16_PCS_ERROR_STATUS_dup3',0x121F0210 => 'PCS_GOPX16_PCS_ERROR_STATUS_dup4', 0x122F0210 => 'PCS_GOPX16_PCS_ERROR_STATUS_dup5'}
reg_list = [ 0x120F0210,0x121F0210, 0x122F0210]
for i in [0,1,2,3]
toollib = Orclib::Toollib2(i)
    for reg in reg_list
        value = toollib.reg_smn_read32(reg).to_s(2)
        puts "GPU#{i.to_s} #{register_map[reg]} => #{value}"
        if value.include?('1')
            puts reg.to_s + " =>  find ERROR at GPU#{i.to_s}"
        end
    end
end
