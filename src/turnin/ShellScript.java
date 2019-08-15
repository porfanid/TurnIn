/*
 * The MIT License
 *
 * Copyright 2019 porfanid.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */
package turnin;

import java.io.BufferedWriter;
import java.io.Closeable;
import java.io.File;
import java.io.FileWriter;
import java.io.Flushable;
import java.io.IOException;

/**
 *
 * @author porfanid
 */
public class ShellScript implements Closeable,Flushable{
    
    private final StringBuilder script;
    private final File scriptFile;
    private boolean isOpen;
    
    public ShellScript(File file,Type type) {
        script=new StringBuilder();
        //String type="#!/bin/bash\n";
        script.append(type.command);
        scriptFile=file;
        isOpen=true;
    }
    public boolean addLine(String line)
    {
        if(isOpen)
        {
            script.append(line).append("\n");
            return true;
        }
        return false;
    }

    @Override
    public void close() throws IOException {
        flush();
        //scriptFile
        isOpen=false;
    }

    @Override
    public void flush() throws IOException {
        if(isOpen)
        {
            BufferedWriter writer = new BufferedWriter(new FileWriter(scriptFile));
            writer.write(script.toString());
            writer.close();
        }else{
            throw new IOException("File is not open");
        }
    }
    
    public String toString()
    {
        return script.toString();
    }
}
