// add this to the end of the 'top' module in build/top.v

  `ifdef BENCH
  always @(posedge clk)
  begin
   	  if(uart_valid)
	  begin
		  $write("%c", memory_mem_wdata[7:0] );
		  $fflush(32'h8000_0001);
	  end
  end
  `endif
