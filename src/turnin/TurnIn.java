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

import java.io.File;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;

import com.jcraft.jsch.*;
import java.io.Closeable;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.PrintStream;
import java.net.UnknownHostException;
import java.util.Scanner;
import java.util.logging.Level;
/**
 *
 * @author porfanid
 */
public class TurnIn implements Runnable,Closeable{

    public static final String UPLOADTO="turnInFiles";
    
    public static final IP SERVER=getProxy();
    
    private final ArrayList<String> args;
    
    private final HashMap<String,String> PROPERTIES;
    
    private final UserInterface user;
    
    private ArrayList<Assignment> list;
    
    private final boolean isAPI;
    
    public TurnIn(String[] cmdArgs,boolean isAPI)
    {
        IP.initialize();
        args=new ArrayList<>(Arrays.asList(cmdArgs));
        PROPERTIES=new HashMap<>();
        user=GetUser.test();
        list=user.getAssignments();
        if(list.isEmpty())
        {
            user.getOutputStream().println("No assignments were submitted. No need to turn in. Exiting.");
            System.exit(0);
        }
        this.isAPI=isAPI;
    }
    
    public TurnIn(String[] cmdArgs)
    {
        this(cmdArgs,false);
    }
    
    
    private static IP getProxy()
    {
        try {
            return new IP("scylla.cs.uoi.gr");
        } catch (UnknownHostException ex) {
            return null;
        }
    }
    
    
    public ChannelSftp getSFTP(Session session) throws JSchException
    {
            ChannelSftp sftpChannel = (ChannelSftp) session.openChannel("sftp");
            sftpChannel.connect();
            return sftpChannel;
    }
    
    public ChannelExec getSSH(Session session) throws JSchException
    {
        ChannelExec channel=(ChannelExec)session.openChannel("exec");
        return channel;
    }
    public String runCommand(Session session,String command) throws IOException, JSchException
    {
        return runCommand(session,command,true);
    }
    
    public String runCommand(Session session,String command,boolean readOutput) throws IOException, JSchException
    {
        ChannelExec channel=getSSH(session);
        channel.setCommand(command);
        channel.setPty(false);
        
        channel.connect();
        if(readOutput)
        {
            InputStream in=channel.getInputStream();
            InputStream out=channel.getErrStream();
            //channel.connect();
            Scanner s=new Scanner(in);
            Scanner err=new Scanner(out);
            String output="";
            while(s.hasNextLine())
            {
                output+=s.nextLine()+"\n";
            }
            while(err.hasNextLine())
            {
                output+=err.nextLine()+"\n";
            }
            try{
                output=output.substring(0, output.length()-1);
            }catch(StringIndexOutOfBoundsException e)
            {

            }

            return output;
        }else
        {
            return "";
        }
    }
    
    public String getFileFromServer(ChannelSftp sftpChannel,String remoteFile) throws SftpException
    {
        InputStream inputStream = sftpChannel.get(remoteFile);
        String text="";
            try (Scanner scanner = new Scanner(inputStream)) {
                while (scanner.hasNextLine()) {
                    String line = scanner.nextLine();
                    text+=(line)+"\n";
                }
            }
            return text;
    }
    
    public boolean isPrimary()
    {
        return args.isEmpty();
    }
    
    /**
     * @param args the command line arguments
     */
    public static void main(String[] args) { 
        Runnable turnIn=new TurnIn(args);  
        turnIn.run();
    }
    
    public Server[] getServers(Session session) throws IOException, JSchException
    {
        String output=runCommand(session,"ruptime");
        
        //System.out.println(output);
        
        String[] lines=output.split("\n");
        
        String[][] data=new String[lines.length][];
        
        for(int i=0;i<lines.length;i++)
        {
            
            lines[i]=lines[i].trim().replaceAll(" +", " ");
            String[] temp=lines[i].split(" ");
            //System.out.println(i+" : "+lines[i]);
            data[i]=temp;
        }
        
        Server[] serverList=new Server[data.length];
        
        
        
        for(int i=0;i<data.length;i++)
        {
            String host=data[i][0];
            String up=data[i][1];
            String users;
            try{
                users=data[i][3];
            }catch(Exception e)
            {
                users="-1";
            }
            
            serverList[i]=new Server(host,up,users);
        }
        return serverList;
    }
    

    @Override
    public void run() {
        boolean hasBeenSubmited=false;
        
        //File home=new File(System.getProperty("user.home"));
            
        //home=new File("../");
            
            //ArrayList<File> hello=FileSearch.run(home, "Hello.txt");
            
            //System.out.println(user);
            //System.out.println(home.getAbsolutePath());
        
        
        
        
            
        Server proxy=new Server("scylla.cs.uoi.gr","up","0");
        
        Session session=proxy.connect(user,null)[0];
        

        try {
            Server[] servers=getServers(session);
            ArrayList<Server> activeServers=new ArrayList<>();
            for(Server i:servers)
            {
                if(i.canConnect&&i.up)
                {
                    activeServers.add(i);
                }
            }
            
            
            File remoteHome=new File(runCommand(session,"pwd"));
            
            
            ChannelSftp channelSftp=getSFTP(session);
            
            
            for(Assignment i:list)
            {
                i.hasBeenUploaded=i.uploadFile(channelSftp, UPLOADTO);
            }
            
            //System.out.println(runCommand(session,"hostname"));
            session.disconnect();
            
            Server main=activeServers.get(0);
            
            Session[] sessions=main.connect(user,proxy);
            
            session=sessions[1];
            
            
            
            
            
            
            hasBeenSubmited=submit(session);
            
            //this.user.getOutputStream().println(hasBeenSubmited);
            
            
            
            
            
            
            //System.out.println(runCommand(session,toString()));
            
            //System.out.println("rm -R "+uploadTo);
            
            //String result=runCommand(session,"rm -R"+uploadTo);
            
            //String command=toString();
            
            
            
            //System.out.println(result);
            
            for(Session i:sessions)
            {
                i.disconnect();
            }
            close();
            
        } catch (IOException | JSchException  ex) {
            java.util.logging.Logger.getLogger(TurnIn.class.getName()).log(Level.SEVERE, null, ex);
            System.exit(1);
        }
        if(hasBeenSubmited)
        {
            user.getOutputStream().println("The files where submitted successfully");
            System.exit(0);
        }
        else
        {
            user.getErrorStream().println("Something went wrong during the procedure");
            System.exit(1);
        }
    }
    
    private boolean submit(Session session) throws JSchException, IOException
    {
        String command=toString();
        String out=runCommand(session,command,true);
        //System.out.println(out);
        return out.contains("COMPLETE");
    }
    
    
    
    
    
    @Override
    public String toString()
    {
        String command;
        if(isPrimary())
        {
        
            
            String lesson=user.getLesson();
            
            String assignments="";
            
            for(Assignment i:list)
            {
                assignments+=i.getPath("/")+" ";
            }
            
            try{
                assignments=assignments.substring(0, assignments.length()-1);
            }catch(StringIndexOutOfBoundsException e)
            {}
            command="yes | turnin "+lesson+" "+assignments;
            
            
        }else{
            command="";
            
            command = args.stream().map((i) -> i+" ").reduce(command, String::concat);
            
            command=command.substring(0, command.length()-1);
        }
        return command;
    }

    @Override
    public void close() throws IOException {
        this.PROPERTIES.clear();
        this.args.clear();
        this.user.close();
    }
    
}