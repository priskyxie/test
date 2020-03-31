require 'orclib'

# PCS_GOPX16_PCS_ERROR_STATUS_dup3/4/5 0x120F0210,
RESULT = true
reg_list = [0x120F0210, 0x121F0210, 0x122F0210]
for i in [0,1,2,3]
toollib = Orclib::Toollib2(i)
    for reg in reg_list
        toollib.reg_smn_write32(reg, 0xFFFFFFFF)
        sleep(0.5)
        value = toollib.reg_smn_read32(reg).to_s(2)
        puts value
       if value.include?('1')
        #    puts reg.to_s + "find ERROR at GPU#{i.to_s}"
        RESULT = false
        end
    end
end
if RESULT
    puts 'all registers clear done'
else
    puts "please do again"
end


