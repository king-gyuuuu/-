import sys

def hex_to_binary(hex_str):
    """16진수 문자열을 이진수 문자열로 변환합니다."""
    return bin(int(hex_str, 16))[2:].zfill(len(hex_str) * 4)

def parse_sic_xe_instruction(hex_code, pc_value, base_value):
    """
    SIC/XE 명령어 (16진수)를 분석하여 세부 정보를 반환합니다.
    Args:
        hex_code (str): 분석할 16진수 명령어.
        pc_value (int): 현재 PC 레지스터 값.
        base_value (int): 현재 Base 레지스터 값.
    Returns:
        dict: 분석된 정보를 담은 딕셔너리.
    """
    hex_code = hex_code.upper()
    try:
        binary_code = hex_to_binary(hex_code)
    except ValueError:
        return {"error": "잘못된 16진수 입력입니다."}

    # 명령어 형식 (e 비트) 결정
    # 3바이트(6자리)는 Format 3, 4바이트(8자리)는 Format 4
    if len(hex_code) == 6:
        # Format 3
        opcode_prefix = binary_code[0:6]
        flags = binary_code[6:12]
        disp_addr = binary_code[12:]
        e_bit = flags[5]
        instruction_format = "Format 3"
        disp_addr_val = int(disp_addr, 2)
        
    elif len(hex_code) == 8:
        # Format 4
        opcode_prefix = binary_code[0:6]
        flags = binary_code[6:12]
        disp_addr = binary_code[12:]
        e_bit = flags[5]
        instruction_format = "Format 4"
        disp_addr_val = int(disp_addr, 2)
        
    else:
        # Format 2 (2바이트 명령어)는 이 프로그램이 처리하지 않습니다.
        return {"error": "지원하지 않는 명령어 형식입니다. 6자리 또는 8자리 16진수를 입력해주세요."}

    # Opcode 및 플래그 비트 추출
    hex_opcode_prefix = int(opcode_prefix, 2)
    hex_effective_opcode = hex_opcode_prefix & 0xFC # n, i 비트를 제외한 실제 Opcode
    
    n_bit, i_bit, x_bit, b_bit, p_bit, e_bit = [int(f) for f in flags]

    # 주소 지정 방식 결정 [cite: 5, 6]
    # n, i 비트를 기준으로 주소 지정 방식 분류
    if n_bit == 0 and i_bit == 0:
        if instruction_format == "Format 3":
            addressing_mode = "Simple (SIC direct addressing)"
            # SIC 호환 모드에서는 b,p,e는 무시 [cite: 6]
        elif instruction_format == "Format 4":
            addressing_mode = "Simple (Direct addressing)"
        else:
            addressing_mode = "Simple"
            
    elif n_bit == 1 and i_bit == 1:
        addressing_mode = "Simple"
        
    elif n_bit == 0 and i_bit == 1:
        addressing_mode = "Immediate"
        
    elif n_bit == 1 and i_bit == 0:
        addressing_mode = "Indirect"
    
    # Simple, PC-relative, Base-relative 주소 지정 방식 결정 
    if addressing_mode in ["Simple", "Indirect"]:
        if b_bit == 0 and p_bit == 1:
            addressing_mode += " (PC-relative)"
        elif b_bit == 1 and p_bit == 0:
            addressing_mode += " (Base-relative)"
        elif b_bit == 0 and p_bit == 0:
            if instruction_format == "Format 3":
                addressing_mode += " (Direct)"
            elif instruction_format == "Format 4":
                addressing_mode += " (Absolute)"
    
    # Disp/Addr 값의 부호 처리
    if instruction_format == "Format 3" and b_bit == 0 and p_bit == 1: # PC-relative
        if disp_addr_val & 0x800: # 12비트 최상위 비트가 1이면 음수
            disp_addr_val = disp_addr_val - 4096

    # TA(Target Address) 계산 [cite: 5, 6]
    TA = 0
    if e_bit == 0: # Format 3
        if b_bit == 1 and p_bit == 0: # Base-relative
            TA = base_value + disp_addr_val
        elif b_bit == 0 and p_bit == 1: # PC-relative
            TA = pc_value + disp_addr_val
        elif b_bit == 0 and p_bit == 0: # Direct or Immediate/Indirect
            TA = disp_addr_val
        
    elif e_bit == 1: # Format 4
        TA = disp_addr_val
        
    # 인덱스 주소 지정 방식(x 비트) 적용 
    if x_bit == 1:
        TA += int("0x000090", 16) # 강의자료의 예제 값 사용 [cite: 6]

    # Register A 값은 프로그램 실행 시에 메모리에서 가져와야 하는 값이므로,
    # 여기서는 알 수 없다고 표기합니다.
    register_a_value = "메모리 내용에 따라 결정"

    result = {
        "1. Binary code": binary_code,
        "2. Opcode": f"0x{hex_effective_opcode:02X}",
        "3. Flag bit": f"n={n_bit}, i={i_bit}, x={x_bit}, b={b_bit}, p={p_bit}, e={e_bit}",
        "4. Addressing mode": addressing_mode,
        "5. Disp/Addr": hex(disp_addr_val) if addressing_mode == "Immediate" else f"{hex(disp_addr_val)} ({disp_addr_val})",
        "6. TA": hex(TA) if addressing_mode != "Immediate" else "TA는 의미 없음 (Immediate 모드)",
        "7. Register A value": register_a_value
    }

    return result

if __name__ == "__main__":
    # PC, Base 레지스터 값 (예제 값, 필요시 수정 가능)
    PC_REGISTER_VALUE = int("003000", 16)
    BASE_REGISTER_VALUE = int("006000", 16)
    
    print("PC 레지스터 값:", hex(PC_REGISTER_VALUE))
    print("Base 레지스터 값:", hex(BASE_REGISTER_VALUE))
    
    # 사용자 입력 받기
    input_hex = input("\n분석할 HEX 코드를 입력하세요 (예: 032600): ").strip()
    if input_hex == "":
        # 엔터만 누르면 기본값 사용
        input_hex = "032600"
        
    print(f"\n입력 HEX 코드: {input_hex}")
    
    result = parse_sic_xe_instruction(input_hex, PC_REGISTER_VALUE, BASE_REGISTER_VALUE)
    
    if "error" in result:
        print(f"오류: {result['error']}")
    else:
        for key, value in result.items():
            print(f"{key}: {value}")