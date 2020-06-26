registration = {}
registration["initialization"] = "r"
registration["ask_user_name"] = "r0"
registration["ask_birth_day"] = "r1"
registration["end"] = "r2"
registration["error"] = "r_err"

qa = {}
qa["initializtion"] = "qa0"
qa["found_question"] = "qa1-1"
qa["fail_to_find_question"] = "qa1-2"
qa["is_correct_question"] = "qa2_t"
qa["not_correct_question"] = "qa2_f"
qa["user_label_answer"] = "qa3"
qa["contact_customer_service"] = "qa4"

high_temp = {}
high_temp["initialization"] = "s1s0"
high_temp["user_not_feeling_well"] = "s1s1"
high_temp["user_feeling_well"] = "s1f1"
high_temp["皮膚出疹"] = "s1d0"
high_temp["眼窩痛"] = "s1d1"
high_temp["喉嚨痛"] = "s1d2"
high_temp["咳嗽"] = "s1d3"
high_temp["咳血痰"] = "s1d4"
high_temp["肌肉酸痛"] = "s1d5"
high_temp["other_symptom"] = "s1df"
high_temp["need_clinic_info"] = "s1s2"
high_temp["dont_need_clinic_info"] = "s1f2"
high_temp["unknown"] = "s1dx_err"
high_temp["end"] = "s1s3"

system = {}
system["wait_customer_system"] = "w"