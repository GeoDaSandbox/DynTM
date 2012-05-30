function DBF(file) { //DBF
	this.file = file;
	this.parse_header();
}
DBF.prototype.parse_header = function(){
	little = new BinaryParser(false,true);
	this.file.skip(4);
	this.numrec = little.toDWord(this.file.read(4));
	var lenhead = little.toWord(this.file.read(2));
	this.file.skip(22);
	field_width = 32;
	numfields = Math.floor((lenhead-33)/field_width);
	this.numfield = numfields;
	var fields = new Array();
	var c = 0;
	var i = 0;
	var rec_size = 0;
	for (i=0;i<numfields;i+=1){
		data = this.file.read(field_width);
		name = data.slice(0,11);
		name = name.replace(/\0/g,'');
		type = data.slice(11,12);
		size = little.toByte(data.slice(16,17));
		rec_size+=size;
		deci = little.toByte(data.slice(17,18));
		fields[i] = [name,type,size,deci,'<br>'];
	}
	this.rec_size = rec_size;
	this.header = fields;
	this.file.skip(1); //skip the \r flag
	this.records_start = this.file.tell();//pos;
}
DBF.prototype.fields = function(){
	return this.header;
}
DBF.prototype.get_row = function(row_id){
	pos = row_id*this.rec_size + row_id*1 + this.records_start;
    this.file.seek(pos);
	var row = new Array()
	deletion_flag = this.file.read(1);
	for (var field in this.header){
		typ = this.header[field][1];
		size = this.header[field][2];
		deci = this.header[field][3];
		value = this.file.read(size)
		//value = value.replace(/\0/g,'');
		//value = value.replace(/ /g,'');
		if (typ=='N'){
			if (deci>0){
				value = parseFloat(value);
			}else{
				value = parseInt(value);
			}
		}
		row[field] = value;
	
	}
	return row;
}
DBF.prototype.get_field = function(index){
    if (index>=0){
        column = new Array();
        for (var row=0; row<this.numrec; row+=1){
            column[row] = this.get_row(row)[index];
        }
        return column;
    } else {
        return '';
    }
}

